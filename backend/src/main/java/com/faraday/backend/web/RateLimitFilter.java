package com.faraday.backend.web;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class RateLimitFilter extends OncePerRequestFilter {

    private static final long WINDOW_MS = 60_000;
    private static final int AUTH_LIMIT = 10;     // per IP per minute on /api/auth/*
    private static final int GENERAL_LIMIT = 100; // per IP per minute elsewhere

    private final Cache<String, AtomicInteger> counters = Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofMinutes(2))
            .maximumSize(500_000)
            .build();

    private boolean allow(String baseKey, int limit) {
        long windowId = System.currentTimeMillis() / WINDOW_MS;
        AtomicInteger counter =
                counters.get(baseKey + ":" + windowId, k -> new AtomicInteger(0));
        return counter.incrementAndGet() <= limit;
    }

    private String clientIp(HttpServletRequest req) {
        String fwd = req.getHeader("X-Forwarded-For");
        if (fwd != null && !fwd.isBlank()) {
            return fwd.split(",")[0].trim();
        }
        return req.getRemoteAddr();
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        boolean authPath = req.getRequestURI().startsWith("/api/auth/");
        String key = (authPath ? "auth:" : "gen:") + clientIp(req);
        int limit = authPath ? AUTH_LIMIT : GENERAL_LIMIT;
        if (allow(key, limit)) {
            chain.doFilter(req, res);
        } else {
            res.setStatus(429);
            res.setHeader("Retry-After", "60");
            res.setContentType("application/json");
            res.getWriter().write("{\"error\":\"rate_limited\"}");
        }
    }
}
