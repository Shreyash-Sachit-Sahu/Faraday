package com.faraday.backend.repo;

import com.faraday.backend.domain.AuthProvider;
import com.faraday.backend.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    Optional<User> findByAuthProviderAndProviderSubject(AuthProvider provider, String subject);
}
