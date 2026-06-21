package tui

import (
	"context"
	"fmt"

	"github.com/figuramax/c4reqber-tui-v9/api"
)

func ensureAPIAuth(ctx context.Context, c *api.Client) error {
	email, password, name := api.AuthCredentials()
	if !api.HasAuthCredentials() {
		if api.DemoAuthAllowed() {
			email = "kilo-v9@test.com"
			password = "test12345"
			name = "Kilo v9"
		} else {
			return fmt.Errorf("set C4_API_EMAIL and C4_API_PASSWORD (or C4_DEMO_AUTH=1 for dev)")
		}
	}
	if err := c.Health(ctx); err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}
	if err := c.Register(ctx, email, password, name); err != nil {
		return fmt.Errorf("register failed: %w", err)
	}
	if err := c.Login(ctx, email, password); err != nil {
		return fmt.Errorf("login failed: %w", err)
	}
	return nil
}