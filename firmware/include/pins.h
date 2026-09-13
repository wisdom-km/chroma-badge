#pragma once
/* BADGE-42C pin map. Source of truth: hardware/pcb/scripts/design.py */

#include <cstdint>
#include <driver/gpio.h>

namespace pins {

constexpr int BAT_SENSE   = 0;   // ADC1_CH0, VBAT / 2
constexpr int NFC_GPO     = 1;   // ST25DV GPO, open-drain, wake (active low)
constexpr int EPD_PWR_EN  = 2;   // P-MOS gate, active low; 10k pull-up, off at boot
constexpr int EPD_BUSY    = 3;   // busy while LOW (GDEM042F86 p.7 note 5-4)
constexpr int I2C_SDA     = 4;
constexpr int I2C_SCL     = 5;
constexpr int EPD_SCK     = 6;
constexpr int EPD_MOSI    = 7;
constexpr int LED_STAT_n  = 8;   // green, sink, idle HIGH
constexpr int BOOT_n      = 9;   // SW2, 10k pull-up, pressed LOW
constexpr int EPD_CS      = 10;
constexpr int EPD_DC      = 20;
constexpr int EPD_RST     = 21;

constexpr gpio_num_t GPIO_NFC_GPO = GPIO_NUM_1;
constexpr gpio_num_t GPIO_BOOT    = GPIO_NUM_9;
constexpr gpio_num_t GPIO_PWR_EN  = GPIO_NUM_2;

}  // namespace pins
