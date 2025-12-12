package com.wai.wai.controller;

import com.wai.wai.service.WAIService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/wai")
public class WAIController {

    @Autowired
    private WAIService waiService;

    @GetMapping
    public List<Map<String, Object>> getWAI(@RequestParam String githubJsonUrl) {
        return waiService.calculateWAIForAllDays(githubJsonUrl);
    }
}



