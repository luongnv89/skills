package main

import (
	"fmt"
	"time"
)

func greeting(t time.Time) string {
	if t.Hour() < 12 {
		return "Good morning"
	}
	return "Good afternoon"
}

func main() {
	fmt.Println(greeting(time.Now()))
}
