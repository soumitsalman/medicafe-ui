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

  // Empty defaults — override at process start only (never build ARG/ENV):
  //   NUXT_PUBLIC_API_BASE → public.apiBase
  //   NUXT_PUBLIC_API_KEY  → public.apiKey
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
