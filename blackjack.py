"""
    CS121 W18
    BLACKJACK
    RIVER
    3/13/18
    PYTHON 3.6.4
"""

# import modules used by this program
from tkinter import *
import random
import pickle

# for developers only -- shows a console version of the game used for debugging things
SHOW_DEBUG = False


# class for individual cards containing the card's
# suit, rank, and number within the unshuffled deck
class Card:
    # initialize cards values, when a card is created in the Deck
    # class, it will store the cards suit, rank, and number within the deck
    def __init__(self, suit, rank, count):
        self.suit = suit
        self.rank = rank
        self.count = count

    # return cards suit and rank. ex. ('S5' for five of spades)
    def get_card(self):
        return self.suit + self.rank

    # return the cards rank, used later in evaluating the cards value
    def get_rank(self):
        return self.rank

    # returns the cards number within an ordered deck
    def get_count(self):
        return self.count


# class for hands used in keeping track of dealer and player's
# set of cards
class Hand:
    def __init__(self):
        # assign values to each rank, used in assigning a value to a card
        # aces start at 11 and are dropped to 1 in get_value when needed
        self.values = {'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10,
                       'Q': 10, 'K': 10}

        # initialize empty cards array, used in storing hand's cards
        self.cards = []

    # function to get the current cards in the hand
    def get_hand(self):
        return ", ".join(card.get_card() for card in self.cards)

    # adds card to end of hand
    def add_card(self, card):
        self.cards.append(card)

    # function to find the value of the hand
    def get_value(self):
        value = 0
        soft_aces = 0
        # compare the rank of each card with the values variable and add it
        # to the hand's value, counting how many aces are worth 11
        for card in self.cards:
            rank = card.get_rank()
            value += self.values[rank]
            if rank == 'A':
                soft_aces += 1

        # while the hand is over 21, drop aces from 11 to 1 one at a time
        while value > 21 and soft_aces > 0:
            value -= 10
            soft_aces -= 1

        return value

    # a blackjack is 21 made with the first two cards
    def is_blackjack(self):
        return len(self.cards) == 2 and self.get_value() == 21


# class for handling a game's deck
class Deck:
    def __init__(self):
        # suit and ranks used in card creation
        self.suits = ['S', 'H', 'D', 'C']
        self.ranks = ['A', '2', '3', '4', '5', '6',
                      '7', '8', '9', '10', 'J', 'Q', 'K']

        # initialize the deck's card array
        self.cards = []

        # card count is used in assigning the card image from
        # the cards folder
        card_count = 1
        # for each suit and rank create a new Card object
        # in the decks cards array with each suit and rank respectively
        for suit in self.suits:
            for rank in self.ranks:
                self.cards.append(Card(suit, rank, card_count))
                card_count += 1

    # function to shuffle the current deck
    def shuffle(self):
        random.shuffle(self.cards)

    # deal_card returns the first card in the cards array
    def deal_card(self):
        return self.cards.pop(0)

    # function to return the current cards in the deck
    def get_deck(self):
        deck_list = ""
        for card in self.cards:
            deck_list += " " + card.get_card()

        return deck_list


# class containing all of the game's functions
class Blackjack:
    def __init__(self):
        # initialize game variables
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.deck = Deck()
        self.player_score = 0
        self.dealer_score = 0
        self.tie_score = 0

        self.in_game = False

        # true while the dealer's second card is still face down
        self.hole_hidden = False

        # used with pickle in saving the dealer / player / tie scores
        self.scores_file = "scores.data"
        self.load_scores()

        # initialize the playing window
        self.window = Tk()
        self.window.title("Blackjack")

        # image used for the dealer's face down card
        self.card_back = PhotoImage(file="cards/b1fv.gif")

        # create menu bar
        menubar = Menu(self.window)
        self.window.config(menu=menubar)  # set windows Menu to menubar

        # create pull-down for options with Rules, Clear Scores, and Quit
        option_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=option_menu)
        option_menu.add_command(label="Blackjack Rules",
                                command=self.show_rules)
        option_menu.add_command(label="Clear Scores",
                                command=self.clear_scores)
        option_menu.add_separator()
        option_menu.add_command(label="Quit", command=self.window.destroy)

        # frame and buttons for the deal/hit/stand functions
        self.button_frame = Frame(self.window)
        self.button_frame.pack()

        bt_deal = Button(self.button_frame, width=20,
                         height=2, text="Deal", command=self.deal)
        bt_hit = Button(self.button_frame, width=20, height=2,
                        text="Hit", command=self.hit)
        bt_stand = Button(self.button_frame, width=20,
                          height=2, text="Stand", command=self.stand)

        # aligning buttons in a row
        bt_deal.grid(row=1, column=1, pady=2)
        bt_hit.grid(row=1, column=2, pady=2)
        bt_stand.grid(row=1, column=3, pady=2)

        # frame for the dealer and players cards and the label
        # and image lists, used in holding which cards should be
        # drawn to the screen
        self.dealer_frame = Frame(self.window)
        self.dealer_frame.pack()
        self.dealer_label_list = []
        self.dealer_image_list = []

        self.player_frame = Frame(self.window)
        self.player_frame.pack()
        self.player_label_list = []
        self.player_image_list = []

        # game status GUI
        self.game_status = Label(self.window, text="Press Deal to start!")
        self.game_status.pack()

        # frame for dealer / player status
        self.status_frame = Frame(self.window)
        self.status_frame.pack(side=LEFT)

        # dealer status GUI
        self.dealer_status = Label(self.status_frame, text="")
        self.dealer_status.pack()

        # player status GUI
        self.player_status = Label(self.status_frame, text="")
        self.player_status.pack()

        # frame for wins / losses / pushes
        self.score_frame = Frame(self.window)
        self.score_frame.pack(side=RIGHT)

        # wins (player score) GUI
        self.player_score_label = Label(self.score_frame)
        self.player_score_label.pack()

        # losses (dealer score) GUI
        self.dealer_score_label = Label(self.score_frame)
        self.dealer_score_label.pack()

        # pushes (tie score) GUI
        self.tie_score_label = Label(self.score_frame)
        self.tie_score_label.pack()

        self.update_score_labels()

    # show the rules of Blackjack
    def show_rules(self):
        help_window = Toplevel(self.window)  # Create a second window
        help_window.title("Rules")

        label = Label(help_window, text="\t\t\tGoal:\n\n"
                      "Beat the dealer by gathering a hand that's as close to 21", justify=LEFT, pady=15)
        label2 = Label(help_window, text="\t\t\t               Rules:\n\n"
                       "1. Aces are worth 11, unless that would put the hand\n"
                       "   over 21, then they are worth 1\n\n"
                       "2. Face cards (King, Queen, Jack) are worth 10 points\n\n"
                       "3. A player will bust when their hand exceeds 21\n\n"
                       "4. The Dealer will deal two cards to you and two to themselves,\n"
                       "   with one of the dealer's cards face down\n\n"
                       "5. 21 with your first two cards is a Blackjack and wins right away\n\n"
                       "6. The player can hit to add cards to their hand\n\n"
                       "7. The player can stand if they are content with their hand\n\n"
                       "8. The Dealer draws until their hand is at least 17\n\n"
                       "9. The player can deal to start a new game", justify=LEFT, padx=50, pady=20)

        label.pack()  # Place the object of the game label in the window
        label2.pack()  # Place the rules label in the window

    # load the saved dealer / player / tie scores from the scores.data file
    def load_scores(self):
        try:
            with open(self.scores_file, 'rb') as score_pickle:
                saved_scores = pickle.load(score_pickle)
            self.dealer_score = int(saved_scores[0])
            self.player_score = int(saved_scores[1])
            # older score files only saved the dealer and player scores
            if len(saved_scores) > 2:
                self.tie_score = int(saved_scores[2])
        except Exception:
            # missing or corrupted scores file, start from zero
            self.dealer_score = 0
            self.player_score = 0
            self.tie_score = 0

    # save the dealer / player / tie scores in the scores.data file
    def save_scores(self):
        try:
            with open(self.scores_file, 'wb') as score_pickle:
                pickle.dump([self.dealer_score, self.player_score,
                            self.tie_score], score_pickle)
        except OSError:
            # scores just won't be saved
            pass

    # function to clear the cards from the canvas
    # and reset label text
    def clear(self):
        # start off by clearing the dealer and player
        # status UI elements
        self.dealer_status["text"] = ""
        self.player_status["text"] = ""

        # destroy each card label on the screen and clear the
        # player and dealers image/label lists, otherwise problems
        # with the UI will happen when the player deals a new deck
        for label in self.player_label_list + self.dealer_label_list:
            label.destroy()
        self.player_label_list.clear()
        self.player_image_list.clear()
        self.dealer_label_list.clear()
        self.dealer_image_list.clear()

        self.hole_hidden = False

    # function for the clear scores option in the menu bar
    # resets dealer, player, and tie scores and clears the
    # scores.data file and GUI labels
    def clear_scores(self):
        self.dealer_score = 0
        self.player_score = 0
        self.tie_score = 0
        self.save_scores()
        self.update_score_labels()

    # draw a card to the screen, by using the cards "count" number we can find the
    # appropriate image from the cards folder, face down cards use the card back image
    def show_card(self, frame, label_list, image_list, card, face_down=False):
        if face_down:
            image = self.card_back
        else:
            image = PhotoImage(file="cards/" + str(card.get_count()) + ".gif")
        image_list.append(image)
        label = Label(frame, image=image)
        label.pack(side=LEFT)
        label_list.append(label)

    # turn the dealer's face down card over
    def reveal_hole_card(self):
        if self.hole_hidden:
            image = PhotoImage(
                file="cards/" + str(self.dealer_hand.cards[1].get_count()) + ".gif")
            self.dealer_image_list[1] = image
            self.dealer_label_list[1]["image"] = image
            self.hole_hidden = False
            self.update_values()

    # function for deal button which resets UI elements and creates a new
    # deck for the dealer and player
    def deal(self):

        # clear the intro status text after the player deals
        self.game_status["text"] = ""

        # clear the cards from the last game
        self.clear()

        # create new deck and shuffle it
        self.deck = Deck()
        self.deck.shuffle()

        # initialize the dealer and players hand
        self.player_hand = Hand()
        self.dealer_hand = Hand()

        # start the game off by adding two cards to each hand
        for i in range(2):
            self.player_hand.add_card(self.deck.deal_card())
            self.dealer_hand.add_card(self.deck.deal_card())

        # draw the cards to the screen, the dealer's second card is dealt face down
        for card in self.player_hand.cards:
            self.show_card(self.player_frame, self.player_label_list,
                           self.player_image_list, card)
        self.show_card(self.dealer_frame, self.dealer_label_list, self.dealer_image_list,
                       self.dealer_hand.cards[0])
        self.show_card(self.dealer_frame, self.dealer_label_list, self.dealer_image_list,
                       self.dealer_hand.cards[1], face_down=True)
        self.hole_hidden = True

        # set in_game to true which allows the user to
        # active the hit and stand buttons
        self.in_game = True

        # after the cards have been dealt, update the dealer and player values
        # to represent the newly added cards
        self.update_values()

        # if either hand is a blackjack the game is over right away
        player_blackjack = self.player_hand.is_blackjack()
        dealer_blackjack = self.dealer_hand.is_blackjack()
        if player_blackjack or dealer_blackjack:
            self.reveal_hole_card()
            if player_blackjack and dealer_blackjack:
                self.finish("tie", "Both have Blackjack, it's a tie!")
            elif player_blackjack:
                self.finish("player", "Blackjack! Player wins!")
            else:
                self.finish("dealer", "Dealer has Blackjack, dealer wins!")

    # if the game is currently active then hit
    def hit(self):
        if self.in_game:
            # add a new card to the player's hand and draw it to the screen
            card = self.deck.deal_card()
            self.player_hand.add_card(card)
            self.show_card(self.player_frame, self.player_label_list,
                           self.player_image_list, card)

            # update the score UI for the dealer and player
            self.update_values()

            # check if the player busted which lets the dealer win
            if self.player_hand.get_value() > 21:
                self.reveal_hole_card()
                self.finish("dealer", "Player busted, dealer wins!")
            # the player can't do better than 21 so stand for them
            elif self.player_hand.get_value() == 21:
                self.stand()
        # if the game is not in play then prompt the user to deal a new deck to play
        else:
            self.show_deal_error()

    # function used in updating the hand values and the UI representing it
    def update_values(self):
        # while the dealer's second card is face down only show the first card's value
        if self.hole_hidden:
            shown_hand = Hand()
            shown_hand.add_card(self.dealer_hand.cards[0])
        else:
            shown_hand = self.dealer_hand
        self.dealer_status["text"] = "Dealer total: " + \
            str(shown_hand.get_value())
        self.player_status["text"] = "Player total: " + \
            str(self.player_hand.get_value())
        if SHOW_DEBUG:
            print("\nDealer:", self.dealer_hand.get_hand(),
                  "total:", self.dealer_hand.get_value())
            print("Player:", self.player_hand.get_hand(),
                  "total:", self.player_hand.get_value())

    # function used in updating the dealer / player / tie score UI
    def update_score_labels(self):
        self.player_score_label["text"] = "Wins: %d" % self.player_score
        self.dealer_score_label["text"] = "Losses: %d" % self.dealer_score
        self.tie_score_label["text"] = "Pushes: %d" % self.tie_score

    # function used in updating the game status and score UI
    def update_game_status(self, color, text):
        self.game_status["fg"] = "%s" % color
        self.game_status["text"] = "%s" % text
        self.update_score_labels()
        self.save_scores()

        if SHOW_DEBUG:
            print("\n%s" % text)
            print("\nDealer:", self.dealer_score, "\nPlayer:",
                  self.player_score, "\nTies:", self.tie_score)

    # end the game, giving a point to the winner ("player", "dealer", or "tie")
    def finish(self, winner, text):
        if winner == "player":
            self.player_score += 1
            color = "green"
        elif winner == "dealer":
            self.dealer_score += 1
            color = "red"
        else:
            self.tie_score += 1
            color = "black"

        self.in_game = False
        self.update_game_status(color, text)

    # if the game is active then update the dealers hand and compare scores
    def stand(self):
        if self.in_game:
            # turn over the dealer's face down card
            self.reveal_hole_card()

            # if the dealers value is under 17 then add a new card to their hand
            while self.dealer_hand.get_value() < 17:
                card = self.deck.deal_card()
                self.dealer_hand.add_card(card)
                self.show_card(
                    self.dealer_frame, self.dealer_label_list, self.dealer_image_list, card)

            # update the score values
            self.update_values()

            dealer_value = self.dealer_hand.get_value()
            player_value = self.player_hand.get_value()

            # dealer busts if over 21
            if dealer_value > 21:
                self.finish("player", "Dealer busted, Player wins!")
            # if both dealer and player have an equal scores then it's a tie
            elif dealer_value == player_value:
                self.finish("tie", "Tie!")
            # the dealer wins if they have a score closer to 21
            elif dealer_value > player_value:
                self.finish("dealer", "Dealer wins!")
            # otherwise the player wins
            else:
                self.finish("player", "Player wins!")
        # if the game is not in play then alert the player to deal a new deck to play
        else:
            self.show_deal_error()

    # tell the player to deal a new deck before hitting or standing
    def show_deal_error(self):
        self.game_status["fg"] = "red"
        self.game_status["text"] = "ERROR: Please deal a new deck to continue!"
        if SHOW_DEBUG:
            print("\nERROR: Please deal a new deck to continue!")


# start the game
Blackjack().window.mainloop()
