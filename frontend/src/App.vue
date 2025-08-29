<template>
  <div id="app">
    <LayoutHeader />
    <main class="container mx-auto px-4 py-8">
      <router-view />
    </main>
    <LayoutFooter />
  </div>
</template>

<script setup>
import LayoutHeader from './components/layout/Header.vue'
import LayoutFooter from './components/layout/Footer.vue'
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
}
</style>
    