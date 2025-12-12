package com.wai.wai.model;

import java.time.LocalDate;

public class DailyMetric {
    private LocalDate date;
    private int whaleTxCount;
    private double whaleTxVolumeBtc;
    private double avgWhaleFeeBtc;
    private double maxWhaleTxBtc;

    // Getter / Setter
    public LocalDate getDate() { return date; }
    public void setDate(LocalDate date) { this.date = date; }
    public int getWhaleTxCount() { return whaleTxCount; }
    public void setWhaleTxCount(int whaleTxCount) { this.whaleTxCount = whaleTxCount; }
    public double getWhaleTxVolumeBtc() { return whaleTxVolumeBtc; }
    public void setWhaleTxVolumeBtc(double whaleTxVolumeBtc) { this.whaleTxVolumeBtc = whaleTxVolumeBtc; }
    public double getAvgWhaleFeeBtc() { return avgWhaleFeeBtc; }
    public void setAvgWhaleFeeBtc(double avgWhaleFeeBtc) { this.avgWhaleFeeBtc = avgWhaleFeeBtc; }
    public double getMaxWhaleTxBtc() { return maxWhaleTxBtc; }
    public void setMaxWhaleTxBtc(double maxWhaleTxBtc) { this.maxWhaleTxBtc = maxWhaleTxBtc; }
}
