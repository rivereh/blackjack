const API = 'https://deckofcardsapi.com/api/deck'
const CARD_BACK = 'https://deckofcardsapi.com/static/img/back.png'
const DEAL_DELAY = 350
const STATS_KEY = 'blackjack-stats'

const dealButton = document.querySelector('#deal')
const hitButton = document.querySelector('#hit')
const standButton = document.querySelector('#stand')
const chipButton = document.querySelector('#chip-deal')
const resetStatsButton = document.querySelector('#reset-stats')
const dealerHandElem = document.querySelector('#dealer-hand')
const playerHandElem = document.querySelector('#player-hand')
const dealerScoreElem = document.querySelector('#dealer-score')
const playerScoreElem = document.querySelector('#player-score')
const statusElem = document.querySelector('#status')

const stats = loadStats()

let deckId = ''
let dealerCards = []
let playerCards = []
let holeCardElem = null
let holeHidden = false
let busy = false

dealButton.addEventListener('click', deal)
hitButton.addEventListener('click', hit)
standButton.addEventListener('click', stand)
chipButton.addEventListener('click', deal)
resetStatsButton.addEventListener('click', resetStats)
renderStats()

document.addEventListener('keydown', (e) => {
  if (e.repeat || e.ctrlKey || e.metaKey || e.altKey) return
  const key = e.key.toLowerCase()
  if (key === 'd' && !dealButton.disabled) deal()
  else if (key === 'h' && !hitButton.disabled) hit()
  else if (key === 's' && !standButton.disabled) stand()
})

// ---------- Game flow ----------

async function deal() {
  if (busy) return
  setControls({ deal: false, hit: false, stand: false })
  busy = true
  reset()
  setStatus('Shuffling…')

  try {
    // one request: new shuffled deck + first four cards
    const data = await request(`${API}/new/draw/?count=4`)
    deckId = data.deck_id
    const [p1, d1, p2, d2] = data.cards

    setStatus('')
    await addCard(playerCards, playerHandElem, p1)
    await addCard(dealerCards, dealerHandElem, d1)
    await addCard(playerCards, playerHandElem, p2)
    await addCard(dealerCards, dealerHandElem, d2, true)

    const playerBJ = isBlackjack(playerCards)
    const dealerBJ = isBlackjack(dealerCards)

    if (playerBJ || dealerBJ) {
      await revealHoleCard()
      if (playerBJ && dealerBJ) finish('push', 'Both have Blackjack — push')
      else if (playerBJ) finish('win', 'Blackjack! You win')
      else finish('lose', 'Dealer has Blackjack')
      return
    }

    setStatus('Hit or stand?')
    busy = false
    setControls({ hit: true, stand: true })
  } catch (err) {
    fail(err)
  }
}

async function hit() {
  if (busy) return
  busy = true
  setControls({ hit: false, stand: false })

  try {
    const [card] = await draw(1)
    await addCard(playerCards, playerHandElem, card)
    const total = handValue(playerCards).total

    if (total > 21) {
      await revealHoleCard()
      finish('lose', `Bust with ${total} — dealer wins`)
    } else if (total === 21) {
      busy = false
      await stand()
    } else {
      busy = false
      setControls({ hit: true, stand: true })
    }
  } catch (err) {
    fail(err)
  }
}

async function stand() {
  if (busy) return
  busy = true
  setControls({ hit: false, stand: false })
  setStatus('Dealer’s turn…')

  try {
    await revealHoleCard()

    // dealer stands on all 17s
    while (handValue(dealerCards).total < 17) {
      await sleep(DEAL_DELAY)
      const [card] = await draw(1)
      await addCard(dealerCards, dealerHandElem, card)
    }

    const player = handValue(playerCards).total
    const dealer = handValue(dealerCards).total

    if (dealer > 21) finish('win', `Dealer busts with ${dealer} — you win!`)
    else if (player > dealer)
      finish('win', `${player} beats ${dealer} — you win!`)
    else if (player < dealer)
      finish('lose', `${dealer} beats ${player} — dealer wins`)
    else finish('push', `Push at ${player}`)
  } catch (err) {
    fail(err)
  }
}

function finish(result, message) {
  if (result === 'win') stats.wins++
  else if (result === 'lose') stats.losses++
  else stats.pushes++
  saveStats()
  renderStats()

  setStatus(message, result)
  busy = false
  setControls({ deal: true, hit: false, stand: false })
}

function fail(err) {
  console.error(err)
  setStatus('Couldn’t reach the card dealer. Try dealing again.', 'lose')
  busy = false
  setControls({ deal: true, hit: false, stand: false })
}

function reset() {
  dealerCards = []
  playerCards = []
  holeCardElem = null
  holeHidden = false
  dealerHandElem.replaceChildren()
  playerHandElem.replaceChildren()
  dealerScoreElem.hidden = true
  playerScoreElem.hidden = true
  playerScoreElem.className = 'score'
  dealerScoreElem.className = 'score'
}

// ---------- Saved record ----------

function loadStats() {
  const fresh = { wins: 0, losses: 0, pushes: 0 }
  try {
    const saved = JSON.parse(localStorage.getItem(STATS_KEY))
    if (saved) {
      for (const key in fresh) fresh[key] = Number(saved[key]) || 0
    }
  } catch {
    // storage unavailable or corrupted - start from zero
  }
  return fresh
}

function saveStats() {
  try {
    localStorage.setItem(STATS_KEY, JSON.stringify(stats))
  } catch {
    // storage unavailable - record just won't persist
  }
}

function resetStats() {
  if (!confirm('Reset your wins, losses and pushes?')) return
  stats.wins = 0
  stats.losses = 0
  stats.pushes = 0
  saveStats()
  renderStats()
}

// ---------- Cards & scoring ----------

async function request(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  if (!data.success) throw new Error(data.error || 'Deck API error')
  return data
}

async function draw(count) {
  const data = await request(`${API}/${deckId}/draw/?count=${count}`)
  return data.cards
}

function cardValue(card) {
  if (card.value === 'ACE') return 11
  if (['KING', 'QUEEN', 'JACK'].includes(card.value)) return 10
  return Number(card.value)
}

// Aces count as 11, then drop to 1 one at a time while the hand is over 21
function handValue(cards) {
  let total = 0
  let softAces = 0
  for (const card of cards) {
    total += cardValue(card)
    if (card.value === 'ACE') softAces++
  }
  while (total > 21 && softAces > 0) {
    total -= 10
    softAces--
  }
  return { total, soft: softAces > 0 }
}

function isBlackjack(cards) {
  return cards.length === 2 && handValue(cards).total === 21
}

async function addCard(hand, handElem, card, faceDown = false) {
  hand.push(card)

  const img = document.createElement('img')
  img.className = 'card'
  img.alt = faceDown ? 'Face-down card' : cardName(card)
  img.src = faceDown ? CARD_BACK : card.image
  await img.decode().catch(() => {})
  handElem.appendChild(img)

  if (faceDown) {
    holeCardElem = img
    holeHidden = true
  }

  renderScores()
  await sleep(DEAL_DELAY)
}

async function revealHoleCard() {
  if (!holeHidden) return
  const card = dealerCards[1]
  const img = holeCardElem

  const front = new Image()
  front.src = card.image
  await front.decode().catch(() => {})

  img.classList.add('flipping')
  await sleep(150)
  img.src = card.image
  img.alt = cardName(card)
  img.classList.remove('flipping')

  holeHidden = false
  renderScores()
  await sleep(DEAL_DELAY)
}

function cardName(card) {
  const v = card.value.charAt(0) + card.value.slice(1).toLowerCase()
  const s = card.suit.charAt(0) + card.suit.slice(1).toLowerCase()
  return `${v} of ${s}`
}

// ---------- Rendering ----------

function renderScores() {
  renderScore(playerScoreElem, playerCards)
  // while the hole card is down, only show the up card's value
  renderScore(
    dealerScoreElem,
    holeHidden ? dealerCards.slice(0, 1) : dealerCards,
  )
}

function renderScore(elem, cards) {
  if (cards.length === 0) {
    elem.hidden = true
    return
  }
  const { total, soft } = handValue(cards)
  elem.hidden = false
  elem.textContent = soft && total < 21 ? `Soft ${total}` : total
  elem.classList.toggle('bust', total > 21)
  elem.classList.toggle('twenty-one', total === 21)
}

function renderStats() {
  document.querySelector('#stat-wins').textContent = stats.wins
  document.querySelector('#stat-losses').textContent = stats.losses
  document.querySelector('#stat-pushes').textContent = stats.pushes
}

function setStatus(message, result = '') {
  statusElem.textContent = message
  statusElem.className = 'status' + (result ? ` status-${result}` : '')
}

function setControls(state) {
  if ('deal' in state) {
    dealButton.disabled = !state.deal
    chipButton.hidden = !state.deal
  }
  if ('hit' in state) hitButton.disabled = !state.hit
  if ('stand' in state) standButton.disabled = !state.stand
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
