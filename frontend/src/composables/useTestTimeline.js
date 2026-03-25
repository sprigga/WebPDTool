// frontend/src/composables/useTestTimeline.js
import { ref, computed, onUnmounted, onBeforeMount } from 'vue'
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

    chartInstance.value = echarts.init(chartRef.value)
    updateChart()

    // Add window resize handler
    window.addEventListener('resize', handleResize)
  }

  const handleResize = () => {
    if (chartInstance.value) {
      chartInstance.value.resize()
    }
  }

  const updateChart = () => {
    if (!chartInstance.value) return

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      legend: {
        data: ['通過', '失敗', '中止']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: chartData.value.map(d => d.date)
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '通過',
          type: 'bar',
          stack: 'total',
          data: chartData.value.map(d => d.pass),
          itemStyle: { color: '#67C23A' }
        },
        {
          name: '失敗',
          type: 'bar',
          stack: 'total',
          data: chartData.value.map(d => d.fail),
          itemStyle: { color: '#F56C6C' }
        },
        {
          name: '中止',
          type: 'bar',
          stack: 'total',
          data: chartData.value.map(d => d.abort),
          itemStyle: { color: '#E6A23C' }
        }
      ]
    }

    chartInstance.value.setOption(option)
  }

  const disposeChart = () => {
    window.removeEventListener('resize', handleResize)
    if (chartInstance.value) {
      chartInstance.value.dispose()
      chartInstance.value = null
    }
  }

  // Cleanup on route leave (Vue Router navigation guard)
  onBeforeRouteLeave(() => {
    disposeChart()
  })

  // Cleanup on component unmount
  onUnmounted(() => {
    disposeChart()
  })

  return {
    chartRef,
    chartData,
    initChart,
    updateChart,
    disposeChart
  }
}
