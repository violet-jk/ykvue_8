-- 严格按照 mqtt说明.md 创建的数据表
CREATE TABLE wincc
(
    `id`                       INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `machine_name`             VARCHAR(20)    DEFAULT NULL COMMENT '设备编号',
    `machine_model`            varchar(20)    DEFAULT NULL COMMENT '设备型号',
    `date`                     DATE           DEFAULT NULL COMMENT '日期',
    `time`                     TIME           DEFAULT NULL COMMENT '时间',

    -- 运行时间
    `hours`                    INT            DEFAULT NULL COMMENT '运行小时数(h)',

    -- 电流电压
    `total_current`            DECIMAL(10, 1) DEFAULT NULL COMMENT '总电流(A)',
    `total_voltage`            DECIMAL(10, 1) DEFAULT NULL COMMENT '总电压(V)',

    -- 小室电压 (CELL1-CELL25)
    `cell_1`                   INT            DEFAULT NULL COMMENT '小室电压-1(mV)',
    `cell_2`                   INT            DEFAULT NULL COMMENT '小室电压-2(mV)',
    `cell_3`                   INT            DEFAULT NULL COMMENT '小室电压-3(mV)',
    `cell_4`                   INT            DEFAULT NULL COMMENT '小室电压-4(mV)',
    `cell_5`                   INT            DEFAULT NULL COMMENT '小室电压-5(mV)',
    `cell_6`                   INT            DEFAULT NULL COMMENT '小室电压-6(mV)',
    `cell_7`                   INT            DEFAULT NULL COMMENT '小室电压-7(mV)',
    `cell_8`                   INT            DEFAULT NULL COMMENT '小室电压-8(mV)',
    `cell_9`                   INT            DEFAULT NULL COMMENT '小室电压-9(mV)',
    `cell_10`                  INT            DEFAULT NULL COMMENT '小室电压-10(mV)',
    `cell_11`                  INT            DEFAULT NULL COMMENT '小室电压-11(mV)',
    `cell_12`                  INT            DEFAULT NULL COMMENT '小室电压-12(mV)',
    `cell_13`                  INT            DEFAULT NULL COMMENT '小室电压-13(mV)',
    `cell_14`                  INT            DEFAULT NULL COMMENT '小室电压-14(mV)',
    `cell_15`                  INT            DEFAULT NULL COMMENT '小室电压-15(mV)',
    `cell_16`                  INT            DEFAULT NULL COMMENT '小室电压-16(mV)',
    `cell_17`                  INT            DEFAULT NULL COMMENT '小室电压-17(mV)',
    `cell_18`                  INT            DEFAULT NULL COMMENT '小室电压-18(mV)',
    `cell_19`                  INT            DEFAULT NULL COMMENT '小室电压-19(mV)',
    `cell_20`                  INT            DEFAULT NULL COMMENT '小室电压-20(mV)',
    `cell_21`                  INT            DEFAULT NULL COMMENT '小室电压-21(mV)',
    `cell_22`                  INT            DEFAULT NULL COMMENT '小室电压-22(mV)',
    `cell_23`                  INT            DEFAULT NULL COMMENT '小室电压-23(mV)',
    `cell_24`                  INT            DEFAULT NULL COMMENT '小室电压-24(mV)',
    `cell_25`                  INT            DEFAULT NULL COMMENT '小室电压-25(mV)',

    -- 电压统计
    `max_voltage`              INT            DEFAULT NULL COMMENT '电压最大值(mV)',
    `min_voltage`              INT            DEFAULT NULL COMMENT '电压最小值(mV)',
    `avg_voltage`              DECIMAL(10, 1) DEFAULT NULL COMMENT '平均电压(mV)',
    `voltage_range`            INT            DEFAULT NULL COMMENT '电压极差(mV)',
    `std_deviation`            DECIMAL(10, 4) DEFAULT NULL COMMENT '小室电压标准差(mV)',

    -- 泵和风扇
    `pump_pressure`            DECIMAL(10, 4) DEFAULT NULL COMMENT '泵后压力(MPa)',
    `pump_opening`             DECIMAL(10, 2) DEFAULT NULL COMMENT '泵的开度(Hz)',
    `fan_opening`              DECIMAL(10, 2) DEFAULT NULL COMMENT '风扇开度(Hz)',

    -- 比重和液位
    `specific_gravity`         DECIMAL(10, 4) DEFAULT NULL COMMENT '碱液比重(mg/cm³)',
    `liquid_level`             DECIMAL(10, 2) DEFAULT NULL COMMENT '液位(mm)',

    -- 压力
    `inlet_pressure`           DECIMAL(10, 4) DEFAULT NULL COMMENT '进槽压力(MPa)',
    `oxygen_outlet_pressure`   DECIMAL(10, 4) DEFAULT NULL COMMENT '氧侧出槽压力(MPa)',
    `hydrogen_outlet_pressure` DECIMAL(10, 4) DEFAULT NULL COMMENT '氢侧出槽压力(MPa)',
    `pressure_diff`            DECIMAL(10, 4) DEFAULT NULL COMMENT '电解槽进出口压差(MPa)',
    `sep_pressure_diff`        DECIMAL(10, 4) DEFAULT NULL COMMENT '氢氧侧压差(MPa)',

    -- 温度
    `alkali_inlet_temp`        DECIMAL(10, 2) DEFAULT NULL COMMENT '碱液入口温度(℃)',
    `oxygen_outlet_temp`       DECIMAL(10, 2) DEFAULT NULL COMMENT '氧侧出槽温度(℃)',
    `hydrogen_outlet_temp`     DECIMAL(10, 2) DEFAULT NULL COMMENT '氢气出槽温度(℃)',
    `hydrogen_gas_temp`        DECIMAL(10, 2) DEFAULT NULL COMMENT '氢侧出气温度(℃)',

    -- 流量和浓度
    `hydrogen_flow_meter`      DECIMAL(10, 4) DEFAULT NULL COMMENT '氢气流量',
    `oxygen_in_hydrogen`       INT            DEFAULT NULL COMMENT '氧中氢含量(ppm)',
    `hydrogen_in_oxygen`       INT            DEFAULT NULL COMMENT '氢中氧含量(ppm)',

    -- 能耗
    `current_power`            DECIMAL(10, 4) DEFAULT NULL COMMENT '当前能耗（直流电耗）',

    PRIMARY KEY (`id`),
    KEY `idx_machine_name` (`machine_name`, `machine_model`),
    KEY `idx_date_time` (`date`, `time`)
) ENGINE = InnoDB;

