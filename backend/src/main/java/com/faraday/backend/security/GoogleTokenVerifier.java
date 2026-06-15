package com.faraday.backend.security;

import com.google.api.client.googleapis.auth.oauth2.GoogleIdToken;
import com.google.api.client.googleapis.auth.oauth2.GoogleIdTokenVerifier;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.gson.GsonFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.stereotype.Service;

import java.util.Collections;

@Service
public class GoogleTokenVerifier {

    private final GoogleIdTokenVerifier verifier;

    public GoogleTokenVerifier(@Value("${faraday.google.client-id}") String clientId) {
        this.verifier = new GoogleIdTokenVerifier.Builder(
                new NetHttpTransport(), GsonFactory.getDefaultInstance())
                .setAudience(Collections.singletonList(clientId))
                .build();
    }

    public GoogleIdToken.Payload verify(String idTokenString) {
        try {
            GoogleIdToken token = verifier.verify(idTokenString);
            if (token == null) {
                throw new BadCredentialsException("Invalid Google token");
            }
            GoogleIdToken.Payload payload = token.getPayload();
            if (!Boolean.TRUE.equals(payload.getEmailVerified())) {
                throw new BadCredentialsException("Google email not verified");
            }
            return payload;
        } catch (BadCredentialsException e) {
            throw e;
        } catch (Exception e) {
            throw new BadCredentialsException("Invalid Google token");
        }
    }
}
