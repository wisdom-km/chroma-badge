#pragma once
#include <cstddef>
#include <cstdint>
constexpr int LOW = 0, HIGH = 1, INPUT = 0, OUTPUT = 1;
void digitalWrite(int, int);
int digitalRead(int);
void pinMode(int, int);
uint32_t millis();
void delay(uint32_t);
