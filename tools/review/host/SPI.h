#pragma once
#include <cstdint>
constexpr int MSBFIRST = 1, SPI_MODE0 = 0;
struct SPISettings { SPISettings(int, int, int) {} };
struct SPIClass {
    void begin(int, int, int, int) {}
    void beginTransaction(SPISettings) {}
    void endTransaction() {}
    uint8_t transfer(uint8_t);
};
extern SPIClass SPI;
