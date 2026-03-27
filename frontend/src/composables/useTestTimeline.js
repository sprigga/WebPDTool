// frontend/src/composables/useTestTimeline.js
import { ref, computed, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import * as echarts from 'echarts'

export function useTestTimeline(sessions) {
  const chartRef = ref(null)
  const chartInstance = ref(null)

  const chartData = computed(() => {
    // Group by date for chart
    const grouped = {}
    sessions.value.forEach(session => {
      const date = new Date(session.start_time).toISOString().split('T')[0]
      if (!grouped[date]) {
        grouped[date] = { pass: 0, fail: 0, abort: 0 }
      }
      if (session.final_result === 'PASS') grouped[date].pass++
      else if (session.final_result === 'FAIL') grouped[date].fail++
      else if (session.final_result === 'ABORT') grouped[date].abort++
    })

    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, counts]) => ({
        date,
        ...counts,
        total: counts.pass + counts.fail + counts.abort
      }))
  })

  const initChart = () => {
    if (!chartRef.value) return
    // dispose any existing instance before re-init
    if (chartInstance.value) {
      chartInstance.value.dispose()
    }
    chartInstance.value = echarts.init(chartRef.value)
    updateChart()
    window.addEventListener('resize', handleResize)
  }

  const handleResize = () => {
    if (chartInstance.value) {
      chartInstance.value.resize()
    }
  }

  const updateChart = () => {
    if (!chartInstance.value) return

    const data = chartData.value
    const hasAbort = data.some(d => d.abort > 0)
    const itemCount = data.length
    const font = '"Microsoft JhengHei", "PingFang TC", "Noto Sans TC", sans-serif'
    const totalTests = data.reduce((s, d) => s + d.total, 0)

    // Pass-rate for secondary Y axis
    const passRates = data.map(d =>
      d.total > 0 ? parseFloat((d.pass / d.total * 100).toFixed(1)) : null
    )

    // X axis label: rotate when many dates, show MM-DD when > 7 days
    const xRotate = itemCount > 14 ? 45 : itemCount > 7 ? 30 : 0
    const xFormatter = value => itemCount > 7 ? value.slice(5) : value

    // Legend entries — only include 中止 when there is abort data
    const legendItems = hasAbort
      ? ['通過', '失敗', '中止', '通過率%']
      : ['通過', '失敗', '通過率%']

    const option = {
      textStyle: { fontFamily: font, fontSize: 13 },

      title: {
        text: '測試趨勢',
        subtext: `共 ${itemCount} 天 · ${totalTests} 次測試`,
        left: 'center',
        top: 6,
        textStyle: { fontFamily: font, fontSize: 14, fontWeight: '600', color: '#303133' },
        subtextStyle: { fontFamily: font, fontSize: 11, color: '#909399' }
      },

      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        confine: true,
        backgroundColor: 'rgba(255,255,255,0.97)',
        borderColor: '#dcdfe6',
        borderWidth: 1,
        textStyle: { fontFamily: font, fontSize: 13, color: '#303133' },
        formatter(params) {
          const date = params[0].axisValue
          const bars = params.filter(p => p.seriesType === 'bar' && p.value > 0)
          const ratePt = params.find(p => p.seriesName === '通過率%')
          const total = bars.reduce((s, p) => s + (p.value || 0), 0)
          const lines = bars.map(p =>
            `${p.marker} ${p.seriesName}：<strong>${p.value}</strong> 次`
          ).join('<br/>')
          const rateStr = ratePt?.value != null
            ? `<br/>${ratePt.marker} 通過率：<strong>${ratePt.value}%</strong>`
            : ''
          return `<div style="line-height:1.8;min-width:140px;">
            <div style="font-weight:600;padding-bottom:4px;border-bottom:1px solid #f0f0f0;margin-bottom:4px;">${date}</div>
            ${lines}
            <div style="padding-top:4px;border-top:1px solid #f0f0f0;margin-top:4px;color:#606266;font-size:12px;">
              合計：<strong>${total}</strong> 次${rateStr}
            </div>
          </div>`
        }
      },

      // Legend at bottom — no overlap with axes or title
      legend: {
        data: legendItems,
        bottom: 4,
        left: 'center',
        orient: 'horizontal',
        itemWidth: 12,
        itemHeight: 12,
        itemGap: 20,
        textStyle: { fontFamily: font, fontSize: 12, color: '#606266' }
      },

      // Grid: leave room for left Y axis numbers, right Y axis label+numbers
      // containLabel:true handles dynamic axis label widths automatically
      grid: {
        top: 60,                          // title (2 lines) height
        left: 8,
        right: 8,
        bottom: xRotate > 0 ? 68 : 44,   // legend(24px) + x labels + optional rotation
        containLabel: true
      },

      xAxis: {
        type: 'category',
        data: data.map(d => d.date),
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#dcdfe6' } },
        axisTick: { alignWithLabel: true, lineStyle: { color: '#dcdfe6' } },
        axisLabel: {
          fontFamily: font,
          fontSize: 12,
          color: '#606266',
          rotate: xRotate,
          formatter: xFormatter,
          hideOverlap: true
        }
      },

      yAxis: [
        {
          // Left: test count
          type: 'value',
          minInterval: 1,
          min: 0,
          // No axis name — avoids overlap; the bar colors + legend are self-explanatory
          axisLabel: { fontFamily: font, fontSize: 11, color: '#606266' },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } }
        },
        {
          // Right: pass rate %
          type: 'value',
          min: 0,
          max: 100,
          interval: 25,
          axisLabel: {
            fontFamily: font,
            fontSize: 11,
            color: '#409EFF',
            formatter: '{value}%'
          },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false }
        }
      ],

      series: [
        {
          name: '通過',
          type: 'bar',
          stack: 'total',
          yAxisIndex: 0,
          data: data.map(d => d.pass),
          itemStyle: { color: '#67C23A' },
          emphasis: { itemStyle: { color: '#529b2e' } },
          label: {
            show: itemCount <= 14,
            position: 'inside',
            fontFamily: font,
            fontSize: 11,
            color: '#fff',
            formatter: p => p.value > 0 ? p.value : ''
          }
        },
        {
          name: '失敗',
          type: 'bar',
          stack: 'total',
          yAxisIndex: 0,
          data: data.map(d => d.fail),
          // Round top when no abort (topmost bar)
          itemStyle: { color: '#F56C6C', borderRadius: hasAbort ? [0, 0, 0, 0] : [3, 3, 0, 0] },
          emphasis: { itemStyle: { color: '#c45656' } },
          label: {
            show: itemCount <= 14,
            position: 'inside',
            fontFamily: font,
            fontSize: 11,
            color: '#fff',
            formatter: p => p.value > 0 ? p.value : ''
          }
        },
        ...(hasAbort ? [{
          name: '中止',
          type: 'bar',
          stack: 'total',
          yAxisIndex: 0,
          data: data.map(d => d.abort),
          itemStyle: { color: '#E6A23C', borderRadius: [3, 3, 0, 0] },
          emphasis: { itemStyle: { color: '#b88230' } },
          label: {
            show: itemCount <= 14,
            position: 'inside',
            fontFamily: font,
            fontSize: 11,
            color: '#fff',
            formatter: p => p.value > 0 ? p.value : ''
          }
        }] : []),
        {
          name: '通過率%',
          type: 'line',
          yAxisIndex: 1,
          data: passRates,
          smooth: true,
          symbol: 'circle',
          symbolSize: itemCount > 20 ? 4 : 7,
          lineStyle: { color: '#409EFF', width: 2 },
          itemStyle: { color: '#409EFF', borderColor: '#fff', borderWidth: 2 },
          connectNulls: false,
          z: 10
        }
      ]
    }

    chartInstance.value.setOption(option, true)
  }

  const disposeChart = () => {
    window.removeEventListener('resize', handleResize)
    if (chartInstance.value) {
      chartInstance.value.dispose()
      chartInstance.value = null
    }
  }

  onBeforeRouteLeave(() => { disposeChart() })
  onUnmounted(() => { disposeChart() })

  return { chartRef, chartData, initChart, updateChart, disposeChart }
}
