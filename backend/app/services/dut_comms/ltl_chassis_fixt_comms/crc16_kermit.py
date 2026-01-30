"""
CRC16 Kermit Implementation

CRC16-CCITT variant used by Kermit protocol.
Polynomial: 0x1021 (x^16 + x^12 + x^5 + 1)
Initial value: 0x0000
Final XOR: 0x0000
Reflect input: True
Reflect output: True

Refactored to replace PyCRC.CRC16Kermit dependency.
"""


class CRC16Kermit:
    """
    CRC16 Kermit checksum calculator.

    This is a pure Python implementation of the CRC16-Kermit algorithm.
    Compatible with PyCRC.CRC16Kermit interface.
    """

    def __init__(self):
        self.polynomial = 0x1021
        self.initial_value = 0x0000
        self.final_xor = 0x0000
        self.table = self._make_table()

    def _make_table(self) -> list:
        """Generate CRC lookup table for reflected algorithm"""
        table = []
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8408  # Reflected polynomial
                else:
                    crc >>= 1
            table.append(crc)
        return table

    def calculate(self, data: bytes) -> int:
        """
        Calculate CRC16-Kermit checksum.

        Args:
            data: Input bytes to calculate CRC over

        Returns:
            16-bit CRC value

        Example:
            >>> crc = CRC16Kermit()
            >>> checksum = crc.calculate(b'123456789')
            >>> hex(checksum)
            '0x2189'
        """
        crc = self.initial_value

        for byte in data:
            table_index = (crc ^ byte) & 0xFF
            crc = (crc >> 8) ^ self.table[table_index]

        return crc & 0xFFFF


# Test vectors
if __name__ == '__main__':
    crc = CRC16Kermit()

    # Standard test vector: "123456789"
    test_data = b'123456789'
    result = crc.calculate(test_data)
    expected = 0x2189

    print(f"Test data: {test_data}")
    print(f"Calculated CRC: 0x{result:04X}")
    print(f"Expected CRC:   0x{expected:04X}")
    print(f"Match: {result == expected}")

    # Additional tests
    test_cases = [
        (b'', 0x0000),
        (b'\x00', 0x0000),
        (b'A', 0x538D),
        (b'ABC', 0x3994),
    ]

    print("\n=== Additional Test Cases ===")
    for data, expected_crc in test_cases:
        calculated = crc.calculate(data)
        match = "✓" if calculated == expected_crc else "✗"
        print(f"{match} Data: {data!r:20} -> 0x{calculated:04X} (expected 0x{expected_crc:04X})")
