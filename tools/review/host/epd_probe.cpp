// Compiles production epd.cpp against controlled I/O substitutes.
// BUSY stuck-high / power-off timeout must report failure. Not a real panel.
#include "epd.h"
#include "pins.h"
#include <Arduino.h>
#include <SPI.h>
#include <iostream>
#include <string>
#include <vector>

SPIClass SPI;
uint32_t now_ms = 0, busy_until = 0;
int dc = 0, cs = 1, command = -1, power = 1;
std::string scenario;
std::vector<int> commands;
std::vector<uint8_t> frame;
void pinMode(int, int) {}
void digitalWrite(int pin, int value) {
    if (pin == pins::EPD_DC) dc = value;
    if (pin == pins::EPD_CS) cs = value;
    if (pin == pins::EPD_PWR_EN) power = value;
}
int digitalRead(int) {
    if (scenario == "always-low") return LOW;
    if (scenario == "poweroff-timeout" && command == 0x02) return LOW;
    if (scenario == "refresh-timeout" && command == 0x12) return LOW;
    if (scenario == "always-high") return HIGH;
    return now_ms < busy_until ? LOW : HIGH;
}
uint32_t millis() { return now_ms; }
void delay(uint32_t ms) { now_ms += ms; }
uint8_t SPIClass::transfer(uint8_t b) {
    if (cs != LOW) throw "SPI transfer while CS high";
    if (dc == LOW) {
        command = b;
        commands.push_back(b);
        if (b == 0x04 || b == 0x12 || b == 0x02) busy_until = now_ms + 6;
    } else if (command == 0x10) frame.push_back(b);
    return b;
}
int main(int argc, char** argv) {
    if (argc < 3) return 2;
    scenario = argv[1];
    int color = std::stoi(argv[2]);
    epd::begin();
    bool ok = epd::refresh_solid(static_cast<epd::Color>(color));
    bool pixels = frame.size() == 30000;
    for (auto b : frame) pixels = pixels && b == color * 85;
    std::cout << "{\"scenario\":\"" << scenario << "\",\"color\":" << color
              << ",\"reported_success\":" << (ok ? "true" : "false")
              << ",\"frame_bytes\":" << frame.size() << ",\"pixels_match\":" << (pixels ? "true" : "false")
              << ",\"rail_off\":" << (power == HIGH ? "true" : "false")
              << ",\"fake_elapsed_ms\":" << now_ms << ",\"commands\":[";
    for (size_t i = 0; i < commands.size(); ++i) std::cout << (i ? "," : "") << commands[i];
    std::cout << "]}\n";
}
