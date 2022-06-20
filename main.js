let deckId = ''

let dealButton = document.querySelector('#deal')
let hitButton = document.querySelector('#hit')
let standButton = document.querySelector('#stand')

dealButton.addEventListener('click', deal)
hitButton.addEventListener('click', hit)
standButton.addEventListener('click', stand)
hitButton.setAttribute('disabled', '')
standButton.setAttribute('disabled', '')

let dealerCardHolder = document.querySelector('.dealers-cards')
let playerCardHolder = document.querySelector('.players-cards')
let dealerValueElem = document.querySelector('.dealer-value')
let playerValueElem = document.querySelector('.player-value')
let statusElem = document.querySelector('.status')
let playerValue = 0
let dealerValue = 0
let gameInProgress = false

async function deal() {
    reset()
    gameInProgress = true

    await fetch('https://deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1')
    .then(res => res.json())
    .then(data => {
        console.log(data)
        deckId = data.deck_id
    }).catch(err => {
        console.log(`Error: ${err}`)
    })

    dealButton.setAttribute('disabled', '')
    hitButton.removeAttribute('disabled')
    standButton.removeAttribute('disabled')
    
    let url = `https://deckofcardsapi.com/api/deck/${deckId}/draw/?count=4`

    fetch(url)
        .then(res => res.json())
        .then(data => {
            // console.log(data)
            // add dealer cards
            for (let i = 0; i < 2; i++) {
                // create card and append to dealer's hand
                let card = document.createElement('img')
                card.src = data.cards[i].image
                dealerCardHolder.appendChild(card)

                // calculate score
                dealerValue += convertToNum(data.cards[i].value, 'dealer')
                dealerValueElem.innerText = dealerValue
            }
            
            // add player cards
            for (let i = 2; i < 4; i++) {
                // create card and add to player's hand
                let card = document.createElement('img')
                card.src = data.cards[i].image
                playerCardHolder.appendChild(card)

                // calculate score
                playerValue += convertToNum(data.cards[i].value, 'player')
                playerValueElem.innerText = playerValue
            }
        }).catch(err => {
            console.log(`Error: ${err}`)
        });
}

function hit()
{
    let url = `https://deckofcardsapi.com/api/deck/${deckId}/draw/?count=1`

    fetch(url)
        .then(res => res.json())
        .then(data => {
            // create card and add to player's hand
            let card = document.createElement('img')
            card.src = data.cards[0].image
            playerCardHolder.appendChild(card)

            // calculate score
            playerValue += convertToNum(data.cards[0].value, 'player')
            playerValueElem.innerText = playerValue

            if (playerValue > 21) {
                statusElem.innerText = 'Player Busted! Dealer wins!'
                endGame()
            }

        }).catch(err => {
            console.log(`Error: ${err}`)
        });
}

async function stand() {
    while (dealerValue < 17) {
        let url = `https://deckofcardsapi.com/api/deck/${deckId}/draw/?count=1`

        await fetch(url)
            .then(res => res.json())
            .then(data => {
                // create card and add to dealers's hand
                let card = document.createElement('img')
                card.src = data.cards[0].image
                dealerCardHolder.appendChild(card)

                // calculate score
                dealerValue += convertToNum(data.cards[0].value, 'dealer')
                dealerValueElem.innerText = dealerValue

                if (dealerValue > 21) {
                    statusElem.innerText = 'Dealer Busted! Player wins!'
                    endGame()
                }

            }).catch(err => {
                console.log(`Error: ${err}`)
            });
    }
    if (gameInProgress)
        calculateScores()
}

function calculateScores() {
    if (playerValue > dealerValue)
        statusElem.innerText = 'Player wins!'
    else if (playerValue < dealerValue)
        statusElem.innerText = 'Dealer wins!'
    else
        statusElem.innerText = 'Tie!'
    endGame()
}

function reset() {
    dealerValue = 0
    playerValue = 0
    dealerValueElem.innerText = 0
    playerValueElem.innerText = 0
    statusElem.innerText = ''

    while (dealerCardHolder.firstChild)
        dealerCardHolder.firstChild.remove()

    while (playerCardHolder.firstChild)
        playerCardHolder.firstChild.remove()
}

function endGame() {
    gameInProgress = false
    dealButton.removeAttribute('disabled')
    hitButton.setAttribute('disabled', '')
    standButton.setAttribute('disabled', '')
}

function convertToNum(val, owner) {
    if (val == 'ACE') {
        if (owner == 'player') {
            if (playerValue + 11 <= 21)
                return 11
            else 
                return 1
        }
        else if (owner == 'dealer') {
            if (dealerValue + 11 <= 21)
                return 11
            else 
                return 1
        }
    }
    else if (val == 'KING' || val == 'QUEEN' || val == 'JACK')
        return 10
    else
        return Number(val)
}