package com.wai.wai.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class DailyMetricsResponse {
    @JsonProperty("generated_at")
    private String generatedAt;

    @JsonProperty("total_days")
    private int totalDays;

    @JsonProperty("daily_metrics")
    private List<DailyMetric> dailyMetrics;

    // Getter + Setter
    public String getGeneratedAt() { return generatedAt; }
    public void setGeneratedAt(String generatedAt) { this.generatedAt = generatedAt; }
    public int getTotalDays() { return totalDays; }
    public void setTotalDays(int totalDays) { this.totalDays = totalDays; }
    public List<DailyMetric> getDailyMetrics() { return dailyMetrics; }
    public void setDailyMetrics(List<DailyMetric> dailyMetrics) { this.dailyMetrics = dailyMetrics; }
}
