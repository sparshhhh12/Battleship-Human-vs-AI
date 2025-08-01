import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import random
import pygame
from datetime import datetime
import pytz

ROWS, COLS = 10, 10
CELL_SIZE = 50

SHIP_INFO = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2
}

SHIP_POINTS = {
    "Carrier": 10,
    "Battleship": 12,
    "Cruiser": 15,
    "Submarine": 15,
    "Destroyer": 20
}

LETTERS = [chr(ord('A') + i) for i in range(ROWS)]

class GameScore:
    def __init__(self, player_score, ai_score, timestamp, game_number):
        self.player_score = player_score
        self.ai_score = ai_score
        self.timestamp = timestamp
        self.game_number = game_number
        self.winner = "Player" if player_score > ai_score else "AI" if ai_score > player_score else "Tie"

    def get_formatted_time(self):
        return self.timestamp.strftime('%H:%M:%S')

class BattleshipGUI:
    def __init__(self, root):
        pygame.mixer.init()
        self.ship_destroyed_sound = "C:\\Users\\Lenovo\\Downloads\\ai project\\explosion_sound.mp3"
    
        self.root = root
        self.player_name = "Player"
        self.root.title(f"Battleship - {self.player_name} vs AI")
        
        # Initialize game history
        self.game_history = []
        self.current_game = 1
        self.total_player_score = 0
        self.total_ai_score = 0
        
        # Set UTC time to 2025-05-11 17:59:02
        self.current_time = datetime.strptime("2025-05-11 17:59:02", "%Y-%m-%d %H:%M:%S")
        self.current_time = pytz.utc.localize(self.current_time)
        
        self.init_game()

    def init_game(self):
        # Initialize scores and move counters
        self.player_score = 0
        self.ai_score = 0
        self.player_moves = 0
        self.ai_moves = 0
        
        self.player_grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.ai_grid = [[None for _ in range(COLS)] for _ in range(ROWS)]

        self.player_ships = {}
        self.ai_ships = {}
        self.ai_ship_cells = set()
        self.ai_guesses = set()
        self.heatmap = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.ai_hits = []
        self.ai_target_mode = False
        self.ai_last_hits = []
        self.ai_target_queue = []
        self.ai_direction = None

        self.selected_ship = None
        self.ship_orientation = None
        self.orientation_var = tk.StringVar(value="None")
        self.ai_sunk_ships = set()
        self.player_sunk_ships = set()
        self.sunk_cells = set()

        # Load images
        self.water_tile = ImageTk.PhotoImage(Image.open("C:\\Users\\Lenovo\\Downloads\\ai project\\water_tile.jpg").resize((CELL_SIZE, CELL_SIZE)))
        self.hit_overlay = ImageTk.PhotoImage(Image.open("C:\\Users\\Lenovo\\Downloads\\ai project\\hit_overlay.jpg").resize((CELL_SIZE, CELL_SIZE)))
        self.miss_overlay = ImageTk.PhotoImage(Image.open("C:\\Users\\Lenovo\\Downloads\\ai project\\miss_overlay.jpg").resize((CELL_SIZE, CELL_SIZE)))
        self.ship_overlay = ImageTk.PhotoImage(Image.open("C:\\Users\\Lenovo\\Downloads\\ai project\\ship_overlay.jpg").resize((CELL_SIZE, CELL_SIZE)))

        self.init_gui()
        self.place_ai_ships()

    def init_gui(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Score display
        self.score_frame = tk.Frame(self.root)
        self.score_frame.grid(row=0, column=0, columnspan=COLS*2+4)
        
        self.player_score_label = tk.Label(self.score_frame, text=f"{self.player_name}: {self.player_score}")
        self.player_score_label.pack(side=tk.LEFT, padx=10)
        
        self.player_moves_label = tk.Label(self.score_frame, text=f"Moves: {self.player_moves}/50")
        self.player_moves_label.pack(side=tk.LEFT, padx=10)
        
        self.ai_score_label = tk.Label(self.score_frame, text=f"AI Score: {self.ai_score}")
        self.ai_score_label.pack(side=tk.LEFT, padx=10)
        
        self.ai_moves_label = tk.Label(self.score_frame, text=f"AI Moves: {self.ai_moves}/50")
        self.ai_moves_label.pack(side=tk.LEFT, padx=10)

        # Game grids
        tk.Label(self.root, text=f"{self.player_name}'s Grid").grid(row=1, column=1, columnspan=COLS)
        for c in range(COLS):
            tk.Label(self.root, text=str(c+1)).grid(row=2, column=c+1)
        for r in range(ROWS):
            tk.Label(self.root, text=LETTERS[r]).grid(row=r+3, column=0)
            for c in range(COLS):
                canvas = tk.Canvas(self.root, width=CELL_SIZE, height=CELL_SIZE, highlightthickness=0, bg="dark blue")
                canvas.grid(row=r+3, column=c+1)
                canvas.create_image(0, 0, anchor='nw', image=self.water_tile)
                canvas.create_line(0, 0, CELL_SIZE, 0, fill="grey", width=2)
                canvas.create_line(0, 0, 0, CELL_SIZE, fill="grey", width=2)
                canvas.create_line(CELL_SIZE, 0, CELL_SIZE, CELL_SIZE, fill="grey", width=2)
                canvas.create_line(0, CELL_SIZE, CELL_SIZE, CELL_SIZE, fill="grey", width=2)
                canvas.bind("<Button-1>", lambda e, r=r, c=c: self.place_ship_prompt(r, c))
                self.player_grid[r][c] = canvas

        offset = COLS + 3
        tk.Label(self.root, text="AI Grid").grid(row=1, column=offset, columnspan=COLS)
        for c in range(COLS):
            tk.Label(self.root, text=str(c+1)).grid(row=2, column=offset+c+1)
        for r in range(ROWS):
            tk.Label(self.root, text=LETTERS[r]).grid(row=r+3, column=offset)
            for c in range(COLS):
                canvas = tk.Canvas(self.root, width=CELL_SIZE, height=CELL_SIZE, highlightthickness=0, bg="dark blue")
                canvas.grid(row=r+3, column=offset+c+1)
                canvas.create_image(0, 0, anchor='nw', image=self.water_tile)
                canvas.create_line(0, 0, CELL_SIZE, 0, fill="grey", width=2)
                canvas.create_line(0, 0, 0, CELL_SIZE, fill="grey", width=2)
                canvas.create_line(CELL_SIZE, 0, CELL_SIZE, CELL_SIZE, fill="grey", width=2)
                canvas.create_line(0, CELL_SIZE, CELL_SIZE, CELL_SIZE, fill="grey", width=2)
                canvas.bind("<Button-1>", lambda e, r=r, c=c: self.player_attack(r, c))
                self.ai_grid[r][c] = canvas

        # Leaderboard
        leaderboard_offset = offset + COLS + 2
        self.create_leaderboard(leaderboard_offset)

        # Ship placement controls
        self.orientation_frame = tk.Frame(self.root)
        self.orientation_frame.grid(row=ROWS+4, column=0, columnspan=COLS)
        tk.Radiobutton(self.orientation_frame, text="Horizontal", variable=self.orientation_var, value="Horizontal").pack(side=tk.LEFT)
        tk.Radiobutton(self.orientation_frame, text="Vertical", variable=self.orientation_var, value="Vertical").pack(side=tk.LEFT)

        self.info_label = tk.Label(self.root, text="Place: Carrier (Size: 5)")
        self.info_label.grid(row=ROWS+5, column=0, columnspan=COLS)

    def create_leaderboard(self, x_position):
        # Leaderboard Frame
        leaderboard_frame = tk.Frame(self.root)
        leaderboard_frame.grid(row=1, column=x_position, rowspan=ROWS+3, sticky="nsew", padx=10)

        # Leaderboard Title
        tk.Label(leaderboard_frame, text="Leaderboard", font=('Arial', 12, 'bold')).pack(pady=2)

        # Create container frame for Treeview and scrollbars
        container = ttk.Frame(leaderboard_frame)
        container.pack(fill='both', expand=True, pady=2)

        # Create Treeview with smaller column widths
        columns = ('Game', 'Score', 'AI', 'Winner')
        self.leaderboard = ttk.Treeview(container, columns=columns, show='headings', height=15)
        
        # Configure columns with smaller widths
        column_widths = {
            'Game': 40,
            'Score': 50,
            'AI': 50,
            'Winner': 50
        }
        
        for col in columns:
            self.leaderboard.heading(col, text=col)
            self.leaderboard.column(col, width=column_widths[col])

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.leaderboard.yview)
        x_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=self.leaderboard.xview)
        
        # Configure treeview to use scrollbars
        self.leaderboard.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Grid layout
        self.leaderboard.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure container grid
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Total scores display
        self.total_score_label = tk.Label(leaderboard_frame, 
                                        text=f"Total Scores:\n{self.player_name}: {self.total_player_score}\nAI: {self.total_ai_score}",
                                        font=('Arial', 9))
        self.total_score_label.pack(pady=5)

    def update_leaderboard(self):
        # Clear existing entries
        for item in self.leaderboard.get_children():
            self.leaderboard.delete(item)
        
        # Add all games to leaderboard
        for game in self.game_history:
            self.leaderboard.insert('', 'end', values=(
                f"Game {game.game_number}",
                game.player_score,
                game.ai_score,
                game.winner
            ))

        # Update total scores
        self.total_score_label.config(
            text=f"Total Scores:\n{self.player_name}: {self.total_player_score}\nAI: {self.total_ai_score}"
        )

    def play_again_prompt(self):
        answer = messagebox.askyesno("Play Again", "Would you like to play another game?")
        if answer:
            # Save current game score
            game_score = GameScore(
                self.player_score,
                self.ai_score,
                self.current_time,
                self.current_game
            )
            self.game_history.append(game_score)
            
            # Update total scores
            self.total_player_score += self.player_score
            self.total_ai_score += self.ai_score
            
            # Increment game counter and update time
            self.current_game += 1
            
            # Start new game
            self.init_game()
            self.update_leaderboard()
        else:
            # Game ended, show final results
            self.show_final_results()

    def show_final_results(self):
        final_winner = self.player_name if self.total_player_score > self.total_ai_score else "AI" if self.total_ai_score > self.total_player_score else "Tie"
        message = f"Final Results after {self.current_game - 1} games:\n\n"
        message += f"Total {self.player_name} Score: {self.total_player_score}\n"
        message += f"Total AI Score: {self.total_ai_score}\n\n"
        message += f"Final Winner: {final_winner}!"
        
        messagebox.showinfo("Game Over - Final Results", message)
        self.root.quit()

    def update_score_display(self):
        self.player_score_label.config(text=f"{self.player_name}: {self.player_score}")
        self.ai_score_label.config(text=f"AI Score: {self.ai_score}")
        self.player_moves_label.config(text=f"Moves: {self.player_moves}/50")
        self.ai_moves_label.config(text=f"AI Moves: {self.ai_moves}/50")

    def check_game_end_by_moves(self):
        if self.player_moves >= 50 and self.ai_moves >= 50:
            winner = self.player_name if self.player_score > self.ai_score else "AI" if self.ai_score > self.player_score else "Tie"
            message = f"Game {self.current_game} Over!\n{self.player_name} Score: {self.player_score}\nAI Score: {self.ai_score}\n"
            if winner == "Tie":
                message += "It's a tie!"
            else:
                message += f"{winner} wins!"
            messagebox.showinfo("Game Over", message)
            self.play_again_prompt()
            return True
        return False

    def play_sound(self, sound_file):
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()

    def set_orientation(self):
        val = self.orientation_var.get()
        return True if val == "Horizontal" else False if val == "Vertical" else None

    def place_ship_prompt(self, r, c):
        for ship, size in SHIP_INFO.items():
            if ship not in self.player_ships:
                orientation = self.set_orientation()
                if orientation is None:
                    messagebox.showinfo("Select Orientation", "Please select orientation first.")
                    return
                if self.valid_placement(self.player_grid, r, c, size, orientation):
                    self.place_ship(self.player_grid, self.player_ships, ship, r, c, size, orientation)
                    if len(self.player_ships) < len(SHIP_INFO):
                        next_ship = list(SHIP_INFO.items())[len(self.player_ships)]
                        self.info_label.config(text=f"Place: {next_ship[0]} (Size: {next_ship[1]})")
                    else:
                        self.info_label.config(text="All ships placed. Start playing!")
                else:
                    messagebox.showerror("Invalid", "Invalid ship placement!")
                break

    def valid_placement(self, grid, r, c, size, horizontal):
        if horizontal:
            if c + size > COLS:
                return False
            return all(self.is_cell_empty(grid, r, c+i) for i in range(size))
        else:
            if r + size > ROWS:
                return False
            return all(self.is_cell_empty(grid, r+i, c) for i in range(size))

    def is_cell_empty(self, grid, r, c):
        ship_dict = self.player_ships if grid is self.player_grid else self.ai_ships
        return (r, c) not in [(rr, cc) for ship_cells in ship_dict.values() for rr, cc in ship_cells]

    def place_ship(self, grid, ship_dict, name, r, c, size, horizontal):
        ship_cells = []
        for i in range(size):
            rr, cc = (r, c+i) if horizontal else (r+i, c)
            ship_cells.append((rr, cc))

        for rr, cc in ship_cells:
            if grid is self.player_grid:
                grid[rr][cc].create_image(0, 0, anchor='nw', image=self.ship_overlay)

        ship_dict[name] = ship_cells

        if grid is self.ai_grid:
            self.ai_ship_cells.update(ship_cells)

    def place_ai_ships(self):
        for ship, size in SHIP_INFO.items():
            placed = False
            while not placed:
                r, c = random.randint(0, ROWS-1), random.randint(0, COLS-1)
                horizontal = random.choice([True, False])
                if self.valid_placement(self.ai_grid, r, c, size, horizontal):
                    self.place_ship(self.ai_grid, self.ai_ships, ship, r, c, size, horizontal)
                    placed = True

    def player_attack(self, r, c):
        if len(self.player_ships) < len(SHIP_INFO):
            messagebox.showinfo("Place All Ships", "You must place all your ships before attacking!")
            return

        if self.player_moves >= 50:
            messagebox.showinfo("Maximum Moves", "You have used all your 50 moves!")
            return

        canvas = self.ai_grid[r][c]
        if canvas.find_withtag("hit") or canvas.find_withtag("miss"):
            return

        self.player_moves += 1
        hit = False

        for ship, cells in self.ai_ships.items():
            if (r, c) in cells:
                canvas.create_image(0, 0, anchor=tk.NW, image=self.hit_overlay, tags="hit")
                canvas.marked = True
                hit = True
                self.player_score += 1
                
                if all(self.ai_grid[rr][cc].find_withtag("hit") for rr, cc in cells):
                    if ship not in self.ai_sunk_ships:
                        self.ai_sunk_ships.add(ship)
                        self.play_sound(self.ship_destroyed_sound)
                        self.player_score += SHIP_POINTS[ship]
                        messagebox.showinfo("Ship Sunk", f"You destroyed the AI's {ship}! +{SHIP_POINTS[ship]} points!")
                        self.root.update()
                        self.sunk_cells.update(cells)
                break
        
        if not hit:
            canvas.create_image(0, 0, anchor=tk.NW, image=self.miss_overlay, tags="miss")
            self.player_score -= 1

        self.update_score_display()

        if self.check_game_end_by_moves():
            return

        if self.check_game_over(self.ai_ships, self.ai_grid):
            messagebox.showinfo("Game Over", f"You win!\nFinal Score - {self.player_name}: {self.player_score}, AI: {self.ai_score}")
            self.root.update()
            self.play_again_prompt()
        else:
            self.root.after(500, self.ai_turn)

    def check_game_over(self, ships, grid):
        return all(all(self.cell_marked(grid[r][c]) for r, c in cells) for cells in ships.values())

    def cell_marked(self, canvas):
        return hasattr(canvas, "marked") and canvas.marked

    def ai_turn(self):
        if self.ai_moves >= 50:
            self.check_game_end_by_moves()
            return

        while True:
            if self.ai_target_queue:
                r, c = self.ai_target_queue.pop(0)
            else:
                self.update_heatmap()
                r, c = self.select_best_target()

            if (r, c) not in self.ai_guesses:
                break

        self.ai_moves += 1
        self.ai_guesses.add((r, c))

        canvas = self.player_grid[r][c]
        hit = False

        for ship, cells in self.player_ships.items():
            if (r, c) in cells:
                canvas.create_image(0, 0, anchor=tk.NW, image=self.hit_overlay, tags="hit")
                canvas.marked = True
                hit = True
                self.ai_score += 1
                self.ai_hits.append((r, c))
                self.ai_last_hits.append((r, c))

                self.ai_target_mode = True
                if len(self.ai_last_hits) >= 2:
                    self.infer_direction_and_enqueue()
                else:
                    self.enqueue_neighbors(r, c)

                if all(self.player_grid[rr][cc].find_withtag("hit") for rr, cc in cells):
                    if ship not in self.player_sunk_ships:
                        self.player_sunk_ships.add(ship)
                        self.play_sound(self.ship_destroyed_sound)
                        self.ai_score += SHIP_POINTS[ship]
                        messagebox.showinfo("Ship Sunk", f"The AI destroyed your {ship}!")
                        self.root.update()

                        self.ai_target_mode = False
                        self.ai_last_hits.clear()
                        self.ai_target_queue = []
                break

        if not hit:
            canvas.create_image(0, 0, anchor=tk.NW, image=self.miss_overlay, tags="miss")
            self.ai_score -= 1

            if self.ai_target_mode and len(self.ai_last_hits) >= 2:
                self.ai_last_hits.pop()

        self.update_score_display()

        if self.check_game_end_by_moves():
            return

        if self.check_game_over(self.player_ships, self.player_grid):
            messagebox.showinfo("Game Over", f"AI wins!\nFinal Score - {self.player_name}: {self.player_score}, AI: {self.ai_score}")
            self.root.update()
            self.play_again_prompt()

    def update_heatmap(self):
        for r in range(ROWS):
            for c in range(COLS):
                if (r, c) in self.ai_guesses or (r, c) in self.sunk_cells:
                    self.heatmap[r][c] = -1
                else:
                    self.heatmap[r][c] = self.estimate_probability(r, c)

    def estimate_probability(self, r, c):
        score = 1
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if (nr, nc) in self.ai_hits:
                    score += 5
        return score

    def select_best_target(self):
        max_val = -1
        best_cells = []
        for r in range(ROWS):
            for c in range(COLS):
                if self.heatmap[r][c] > max_val:
                    max_val = self.heatmap[r][c]
                    best_cells = [(r, c)]
                elif self.heatmap[r][c] == max_val:
                    best_cells.append((r, c))
        return random.choice(best_cells) if best_cells else (0, 0)

    def enqueue_neighbors(self, r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in self.ai_guesses:
                self.ai_target_queue.append((nr, nc))

    def infer_direction_and_enqueue(self):
        (r1, c1), (r2, c2) = self.ai_last_hits[-2], self.ai_last_hits[-1]
        if r1 == r2:
            dr, dc = 0, 1 if c2 > c1 else -1
        elif c1 == c2:
            dr, dc = 1 if r2 > r1 else -1, 0
        else:
            return
        
        for i in range(1, 5):
            nr, nc = r2 + dr*i, c2 + dc*i
            if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in self.ai_guesses:
                self.ai_target_queue.append((nr, nc))
            else:
                for j in range(1, 5):
                    nr, nc = r1 - dr*j, c1 - dc*j
                    if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in self.ai_guesses:
                        self.ai_target_queue.append((nr, nc))
                    else:
                        break
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()