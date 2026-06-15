package com.faraday.backend.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.UUID;

/**
 * Reads the authenticated user id (the UUID string the JWT filter set as the
 * principal) out of the security context, so controllers stay clean.
 */
public final class CurrentUser {

    private CurrentUser() {
    }

    public static UUID id() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || auth.getPrincipal() == null) {
            throw new IllegalStateException("No authenticated user in context");
        }
        return UUID.fromString(auth.getPrincipal().toString());
    }
}
