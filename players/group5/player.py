import os
import numpy as np
import logging

import constants
from players.group5.door import DoorIdentifier
from players.group5.player_map import PlayerMapInterface, SimplePlayerCentricMap, StartPosCentricPlayerMap
from timing_maze_state import TimingMazeState
from players.group5.converge import converge_basic, converge


class G5_Player:
    def __init__(self, rng: np.random.Generator, logger: logging.Logger, precomp_dir: str, maximum_door_frequency: int, radius: int) -> None:
        """Initialise the player with the basic amoeba information

            Args:
                rng (np.random.Generator): numpy random number generator, use this for same player behavior across run
                logger (logging.Logger): logger use this like logger.info("message")
                maximum_door_frequency (int): the maximum frequency of doors
                radius (int): the radius of the drone
                precomp_dir (str): Directory path to store/load pre-computation
        """
        self._setup_logger(logger)
        self.rng = rng
        self.maximum_door_frequency = maximum_door_frequency
        self.radius = radius
        self.player_map: PlayerMapInterface = StartPosCentricPlayerMap(maximum_door_frequency, logger)
        self.turns = 0
        self.mode = 0

    def _setup_logger(self, logger):
        self.logger = logger
        self.logger.setLevel(logging.DEBUG)
        self.log_dir = "./log"
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(self.log_dir, 'Player 5.log'), mode="w")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(fh)

    def simple_search(self):        
        nw, sw, ne, se = 0, 0, 0, 0

        cur_pos = self.player_map.get_cur_pos()
        cur_pos_i, cur_pos_j = cur_pos[0], cur_pos[1]
        for i in range(self.radius):
            for j in range(self.radius):
                if self.player_map.get_seen_counts([[cur_pos_i-i, cur_pos_j-j]])[0]>0:
                    nw += 1
                if self.player_map.get_seen_counts([[cur_pos_i+i, cur_pos_j-j]])[0]>0:
                    sw += 1
                if self.player_map.get_seen_counts([[cur_pos_i-i, cur_pos_j+j]])[0]>0:
                    ne += 1
                if self.player_map.get_seen_counts([[cur_pos_i+i, cur_pos_j+j]])[0]>0:
                    se += 1
        best_diagonal = min(nw, sw, ne, se)
        if best_diagonal == nw:
            if ne > sw:
                return constants.UP
            return constants.LEFT
        elif best_diagonal == sw:
            if se > nw:
                return constants.DOWN
            return constants.LEFT
        elif best_diagonal == ne:
            if nw > se:
                return constants.UP
            return constants.RIGHT
        else:
            if sw > ne:
                return constants.DOWN
            return constants.RIGHT

    def move(self, current_percept: TimingMazeState) -> int:
        """Function which retrieves the current state of the amoeba map and returns an amoeba movement

            Args:
                current_percept(TimingMazeState): contains current state information
            Returns:
                int: This function returns the next move of the user:
                    WAIT = -1
                    LEFT = 0
                    UP = 1
                    RIGHT = 2
                    DOWN = 3
        """
        try:
            self.turns += 1
            self.player_map.update_map(self.turns, current_percept)
            cur_pos = self.player_map.get_cur_pos()
            
            valid_moves = self.player_map.get_valid_moves(self.turns)
            self.logger.debug(f"Valid moves: {valid_moves}")

            # example_freq_set = self.player_map.get_wall_freq_candidates(door_id=DoorIdentifier(absolute_coord=cur_pos, door_type=0))
            # self.logger.debug(f"Example freq set for coordinate {cur_pos}: {example_freq_set}")

            exists, end_pos = self.player_map.get_end_pos_if_known()
            if not exists:
                move = self.simple_search()
                return move if move in valid_moves else constants.WAIT  # TODO: this is if-statement is to demonstrate valid_moves is correct (@eylam, replace with actual logic)
            move = converge(self.player_map.get_cur_pos(), end_pos)
            return move if move in valid_moves else constants.WAIT
        except Exception as e:
            self.logger.debug(e, e.with_traceback)
            return constants.WAIT

