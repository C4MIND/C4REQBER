package api

import "os"

// AuthCredentials from environment (desktop / production).
// C4_API_EMAIL, C4_API_PASSWORD, C4_API_NAME (optional).
func AuthCredentials() (email, password, name string) {
	email = os.Getenv("C4_API_EMAIL")
	password = os.Getenv("C4_API_PASSWORD")
	name = os.Getenv("C4_API_NAME")
	if name == "" {
		name = "c4reqber-user"
	}
	return email, password, name
}

func HasAuthCredentials() bool {
	e, p, _ := AuthCredentials()
	return e != "" && p != ""
}

// DemoAuthAllowed permits hardcoded dev credentials when C4_DEMO_AUTH=1.
func DemoAuthAllowed() bool {
	return os.Getenv("C4_DEMO_AUTH") == "1"
}