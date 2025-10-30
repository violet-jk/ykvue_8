# MQTT 字段映射说明（1号电解槽）

## 字段映射表

| MQTT字段     | 数据库字段                    | 描述         | 单位     |
|------------|--------------------------|------------|--------|
| SYS_T/CM_H | hours                    | 运行小时数      | h      |
| ELE_I      | total_current            | 总电流        | A      |
| ELE_V      | total_voltage            | 总电压        | V      |
| CELL1      | cell_1                   | 小室电压-1     | mV     |
| CELL2      | cell_2                   | 小室电压-2     | mV     |
| CELL3      | cell_3                   | 小室电压-3     | mV     |
| CELL4      | cell_4                   | 小室电压-4     | mV     |
| CELL5      | cell_5                   | 小室电压-5     | mV     |
| CELL6      | cell_6                   | 小室电压-6     | mV     |
| CELL7      | cell_7                   | 小室电压-7     | mV     |
| CELL8      | cell_8                   | 小室电压-8     | mV     |
| CELL9      | cell_9                   | 小室电压-9     | mV     |
| CELL10     | cell_10                  | 小室电压-10    | mV     |
| CELL11     | cell_11                  | 小室电压-11    | mV     |
| CELL12     | cell_12                  | 小室电压-12    | mV     |
| CELL13     | cell_13                  | 小室电压-13    | mV     |
| CELL14     | cell_14                  | 小室电压-14    | mV     |
| CELL15     | cell_15                  | 小室电压-15    | mV     |
| CELL16     | cell_16                  | 小室电压-16    | mV     |
| CELL17     | cell_17                  | 小室电压-17    | mV     |
| CELL18     | cell_18                  | 小室电压-18    | mV     |
| CELL19     | cell_19                  | 小室电压-19    | mV     |
| CELL20     | cell_20                  | 小室电压-20    | mV     |
| CELL21     | cell_21                  | 小室电压-21    | mV     |
| CELL22     | cell_22                  | 小室电压-22    | mV     |
| CELL23     | cell_23                  | 小室电压-23    | mV     |
| CELL24     | cell_24                  | 小室电压-24    | mV     |
| CELL25     | cell_25                  | 小室电压-25    | mV     |
| cell_max   | max_voltage              | 电压最大值      | mV     |
| cell_min   | min_voltage              | 电压最小值      | mV     |
| cell_ave   | avg_voltage              | 平均电压       | mV     |
| cell_range | voltage_range            | 电压极差       | mV     |
| PUMP_P     | pump_pressure            | 泵后压力       | MPa    |
| LCP_OUT    | pump_opening             | 泵的开度       | Hz     |
| FAN_OUT    | fan_opening              | 风扇开度       | Hz     |
| DT118      | specific_gravity         | 碱液比重       | mg/cm³ |
| PT102      | inlet_pressure           | 进槽压力       | MPa    |
| LIT109     | liquid_level             | 液位         | mm     |
| PT104      | oxygen_outlet_pressure   | 氧侧出槽压力     | MPa    |
| PT105      | hydrogen_outlet_pressure | 氢侧出槽压力     | MPa    |
| TT103      | oxygen_outlet_temp       | 氧侧出槽温度     | ℃      |
| TT101      | alkali_inlet_temp        | 碱液入口温度     | ℃      |
| TT106      | hydrogen_outlet_temp     | 氢气出槽温度     | ℃      |
| TT114      | hydrogen_gas_temp        | 氢侧出气温度     | ℃      |
| FIT109     | hydrogen_flow_meter      | 氢气流量       | N/A    |
| AT132      | oxygen_in_hydrogen       | 氧中氢含量      | ppm    |
| AT131      | hydrogen_in_oxygen       | 氢中氧含量      | ppm    |
| 当前能耗       | current_power            | 当前能耗（直流电耗） | N/A    |
| ELE_PDT    | pressure_diff            | 电解槽进出口压差   | MPa    |
| SEP_PDT    | sep_pressure_diff        | 氢氧侧压差      | MPa    |
| 标准差        | std_deviation            | 小室电压标准差    | N/A    |

## 说明

- **MQTT主题格式**: `WinCC/#`
- **数据类型**: 根据Mysql建表语句判断
