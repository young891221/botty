from char import IChar
from logger import Logger
from pather import Location, Pather
from item.pickit import PickIt
import template_finder
from town.town_manager import TownManager
from utils.misc import wait
from ui import waypoint
from ui_manager import wait_until_hidden, wait_until_visible, ScreenObjects, is_visible
from screen import convert_abs_to_monitor, grab
import random

class ShenkEld:

    name = "run_shenk"

    def __init__(
        self,
        pather: Pather,
        town_manager: TownManager,
        char: IChar,
        pickit: PickIt,
        runs: list[str]
    ):
        self._pather = pather
        self._town_manager = town_manager
        self._char = char
        self._pickit = pickit
        self._runs = runs

    def pre_buff_approach(self, start_loc: Location) -> bool | Location:
        Logger.info("Run Eldritch for pre buff")
        if not self._town_manager.open_wp(start_loc):
            return False
        wait(0.4)
        if waypoint.use_wp("Halls of Pain"): # use Halls of Pain Waypoint (5th in A5)
            return Location.A5_NIHLATHAK_START
        return False

    def pre_buff(self, do_pre_buff: bool):
        if do_pre_buff:
            self._char.pre_buff()

        retryCount = 0
        while not self.find_ni_wp():
            Logger.info("Not Found ni wp")
            retryCount += 1
            if retryCount == 2:
                return False
            pos_m = convert_abs_to_monitor((random.randint(-100, 100), random.randint(-100, 100)))
            self._char.pre_move()
            self._char.move(pos_m)

        wait(0.4)
        if waypoint.use_wp("Frigid Highlands"):
            return Location.A5_ELDRITCH_START
        return False

    def find_ni_wp(self):
        found_wp_func = lambda: is_visible(ScreenObjects.WaypointLabel)
        pos_m = convert_abs_to_monitor((-150, -150))
        self._char.pre_move()
        self._char.move(pos_m)
        return self._char.select_by_template(["ni_wp1","ni_wp2","ni_wp3"], found_wp_func, telekinesis=True)

    def approach(self, start_loc: Location) -> bool | Location:
        Logger.info("Run Eldritch")
        # Go to Frigid Highlands
        if not self._town_manager.open_wp(start_loc):
            return False
        wait(0.4)
        if waypoint.use_wp("Frigid Highlands"):
            return Location.A5_ELDRITCH_START
        return False

    def battle(self, do_shenk: bool, do_pre_buff: bool, game_stats) -> bool | tuple[Location, bool]:
        # Eldritch
        game_stats.update_location("Eld")
        if not template_finder.search_and_wait(["ELDRITCH_0", "ELDRITCH_0_V2", "ELDRITCH_0_V3", "ELDRITCH_START", "ELDRITCH_START_V2"], threshold=0.65, timeout=20).valid:
            return False
        #if do_pre_buff:
        #    self._char.pre_buff()
        if self._char.capabilities.can_teleport_natively:
            self._pather.traverse_nodes_fixed("eldritch_safe_dist", self._char)
        else:
            if not self._pather.traverse_nodes((Location.A5_ELDRITCH_START, Location.A5_ELDRITCH_SAFE_DIST), self._char, force_move=True):
                return False
        self._char.kill_eldritch()
        loc = Location.A5_ELDRITCH_END
        wait(0.2, 0.3)
        picked_up_items = self._pickit.pick_up_items(self._char)

        # Shenk
        if do_shenk:
            Logger.info("Run Shenk")
            game_stats.update_location("Shk")
            self._curr_loc = Location.A5_SHENK_START
            # No force move, otherwise we might get stuck at stairs!
            if not self._pather.traverse_nodes((Location.A5_SHENK_START, Location.A5_SHENK_SAFE_DIST), self._char):
                return False
            self._char.kill_shenk()
            loc = Location.A5_SHENK_END
            wait(1.9, 2.4) # sometimes merc needs some more time to kill shenk...
            picked_up_items |= self._pickit.pick_up_items(self._char)

        return (loc, picked_up_items)
