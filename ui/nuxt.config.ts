// https://nuxt.com/docs/api/configuration/nuxt-config
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

  // Empty defaults — set at deploy/runtime via BACKEND_BASE_URL / BACKEND_API_KEY
  // (see server/plugins/backend-env.ts). Never bake these at build time.
  runtimeConfig: {
    public: {
      apiBase: '',
      apiKey: ''
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
