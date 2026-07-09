// https://nuxt.com/docs/api/configuration/nuxt-config
declare const process: { env: Record<string, string | undefined> }

export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui'
  ],

  components: {
    dirs: [
      {
        path: '~/components',
        pathPrefix: false
      }
    ]
  },

  imports: {
    dirs: ['composables']
  },

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      apiBase: process.env.CASES_BASE_URL ?? 'http://localhost:8000',
      apiKey: process.env.CASES_DB_API_KEY ?? ''
    }
  },

  routeRules: {
    '/summary': { redirect: '/billing' },
    '/attestation': { redirect: '/billing' },
    '/case/current': { redirect: '/' }
  },

  compatibilityDate: '2026-06-30',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})
