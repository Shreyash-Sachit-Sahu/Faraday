package com.faraday.backend.web;

import com.faraday.backend.domain.User;
import com.faraday.backend.repo.UserRepository;
import com.faraday.backend.security.CurrentUser;
import com.faraday.backend.web.dto.UserResponse;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserRepository userRepo;

    public UserController(UserRepository userRepo) {
        this.userRepo = userRepo;
    }

    @GetMapping("/me")
    public UserResponse me() {
        User user = userRepo.findById(CurrentUser.id())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED));
        return new UserResponse(
                user.getId(), user.getEmail(), user.getDisplayName(), user.getRole());
    }
}
