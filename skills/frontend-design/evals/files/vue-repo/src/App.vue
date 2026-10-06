<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header class="app-header">
    <RouterLink to="/" class="brand">Acme Console</RouterLink>
    <nav>
      <RouterLink to="/">Overview</RouterLink>
      <RouterLink to="/projects">Projects</RouterLink>
    </nav>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style>
:root {
  --color-ink: #000000;
  --color-surface: #ffffff;
  --color-muted: #6b7280;
  --color-accent: #22c55e;
  --radius: 6px;
  --space: 8px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  padding: calc(var(--space) * 2) calc(var(--space) * 3);
  border-bottom: 1px solid var(--color-muted);
}
</style>
