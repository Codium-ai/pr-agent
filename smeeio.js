const SmeeClient = require('smee-client')

const smee = new SmeeClient({
  source: 'https://smee.io/VlexRkbYt8u4ZYYb',
  target: 'http://localhost:3010/api/v1/github_webhooks',
  logger: console
})

const events = smee.start()

// Stop forwarding events
// events.close()