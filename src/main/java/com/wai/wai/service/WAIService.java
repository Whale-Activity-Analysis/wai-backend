package com.wai.wai.service;

import com.wai.wai.model.DailyMetric;
import com.wai.wai.model.DailyMetricsResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class WAIService {

    private final ObjectMapper objectMapper = new ObjectMapper();

    public List<Map<String, Object>> calculateWAIForAllDays(String githubJsonUrl) {
        List<Map<String, Object>> result = new ArrayList<>();
        try {
            RestTemplate restTemplate = new RestTemplate();
            String json = restTemplate.getForObject(githubJsonUrl, String.class);

            if (json == null || json.isEmpty()) {
                return result;
            }

            DailyMetricsResponse response = objectMapper.readValue(json, DailyMetricsResponse.class);

            List<DailyMetric> metrics = response.getDailyMetrics();
            if (metrics == null || metrics.isEmpty()) {
                return result;
            }

            for (DailyMetric day : metrics) {
                double txCountNorm = Math.min(day.getWhaleTxCount() / 10.0, 1.0);
                double txVolumeNorm = Math.min(day.getWhaleTxVolumeBtc() / 1000.0, 1.0);
                double maxTxNorm = Math.min(day.getMaxWhaleTxBtc() / 1000.0, 1.0);

                double index = (txCountNorm + txVolumeNorm + maxTxNorm) / 3.0 * 100;
                index = Math.round(index);

                result.add(Map.of(
                        "date", day.getDate(),
                        "wai", index
                ));
            }

            return result;

        } catch (Exception e) {
            e.printStackTrace();
            return result;
        }
    }
}

