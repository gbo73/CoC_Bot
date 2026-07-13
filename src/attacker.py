from utils import *
import configs
from configs import *

class Attacker:
    def __init__(self):
        self.assets = Asset_Manager.attacker_assets
        self.misc_assets = Asset_Manager.misc_assets
    
    # ============================================================
    # 📱 Screen Interaction
    # ============================================================
    
    def _click_okay(self, timeout=5):
        return click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["okay"], thresh=0.9),
            timeout=timeout,
        )
    
    def _click_surrender(self, timeout=5):
        return click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["surrender"], thresh=0.9),
            timeout=timeout
        )
    
    def _click_end_battle(self, timeout=5):
        return click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["end_battle"], thresh=0.9),
            timeout=timeout
        )
    
    def _click_return_home(self, timeout=5):
        return click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["return_home"], thresh=0.9),
            timeout=timeout
        )

    def request_free_reinforcements(self, timeout=5):
        """
        Purpose:
        Open My Army, then claim free reinforcements when available.
        """

        import time

        print("### REINFORCEMENT CHECK CALLED ###")
        print("Opening My Army")

        Input_Handler.click(
            0.04,
            0.74
        )

        time.sleep(1.50)

        return self.claim_free_reinforcements(
            timeout=timeout
        )
    
        # Close My Army before continuing
        Input_Handler.click_exit()
        time.sleep(1.00)

        return claimed   

    def claim_free_reinforcements(self, timeout=5):
        """
        Purpose:
        Claim free Clan Castle reinforcements when the FREE button
        is visible in the My Army panel.
        """

        import time

        free_x, free_y = Frame_Handler.locate(
            self.assets["free_reinforcements"],
            thresh=0.85
        )

        if free_x is None or free_y is None:
            print("Free reinforcements not available")
            return False

        print(
            "Free reinforcements detected at",
            free_x,
            free_y
        )

        # Open Add Reinforcements
        Input_Handler.click(
            free_x,
            free_y
        )

        time.sleep(1.50)

        print("Selecting reinforcement troop")

        # Click the balloon card
        Input_Handler.click(
            0.13,
            0.36
        )

        time.sleep(0.80)

        print("Confirming reinforcements")

        # Click the green Confirm button
        Input_Handler.click(
            0.53,
            0.73
        )

        time.sleep(1.50)

        print("Free reinforcements claimed")
        return True

    def get_attack_resources(self):
        """
        Purpose:
        Read the available gold and elixir displayed during matchmaking.
        """

        print("### GET ATTACK RESOURCES CALLED ###")
        section = Frame_Handler.get_frame_section(
            0.00,
            0.10,
            0.27,
            0.32,
            high_contrast=True,
            thresh=200
        )

        if configs.DEBUG:
            Frame_Handler.save_frame(
                section,
                "debug/attack_resources.png"
            )

        import cv2

        # Purpose: Enlarge resource numbers to improve OCR,
        # especially leading digits such as the first "1".
        section = cv2.resize(
            section,
            None,
            fx=2,
            fy=2,
            interpolation=cv2.INTER_CUBIC
        )

        text = OCR_Handler.get_text(section)

        print("Attack resources OCR:", text)

        values = []

        for value in text:
            original_digits = "".join(
                character
                for character in value
                if character.isdigit()
            )

            # Ignore labels and OCR noise such as "Available Loot:"
            if len(original_digits) < 3:
                continue

            number = int(original_digits)
            values.append(number)

        # Keep only the last three detected numbers:
        # gold, elixir and dark elixir
        values = values[-3:]

        if len(values) < 3:
            raise Exception(
                "Failed to read attack gold, elixir and dark elixir"
            )

        gold = values[0]
        elixir = values[1]
        dark_elixir = values[2]

        # OCR sometimes drops the first digit of dark elixir.
        # Example: 1838 may be read as 838.
        if dark_elixir < 1000:
            dark_elixir += 1000

        print(
            "Available resources |",
            "gold =", gold,
            "| elixir =", elixir,
            "| dark_elixir =", dark_elixir
        )

        return {
            "gold": gold,
            "elixir": elixir,
            "dark_elixir": dark_elixir
        }


    def start_normal_attack(self, timeout=60):
        import time
        
        # Click attack
        Input_Handler.click(0.07, 0.9)
        
        # Find a match
        def locate_find_a_match():
            xys = Frame_Handler.locate(self.assets["find_a_match"], thresh=0.9, return_all=True)
            if len(xys) == 0: return None, None
            xys = sorted(xys, key=lambda xy: xy[0])
            x, y = xys[0]
            if x > 0.2: return None, None
            return x, y
        if not click_with_timeout(
            locate_find_a_match,
            timeout=5
        ): return False
        
        # Confirm attack
        if not click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["confirm_attack"], thresh=0.9),
            timeout=5
        ): return False
        
        # Wait until "end battle" button is found
        start_time = time.time()
        search_count = 0

        while time.time() - start_time < timeout:
            x, y = Frame_Handler.locate(
                self.assets["end_battle"],
                thresh=0.9
            )

            if x is not None and y is not None:
                try:
                    print("### START RESOURCE CHECK ###")

                    resources = self.get_attack_resources()

                    gold_ok = (
                        resources["gold"]
                        >= MIN_ATTACK_GOLD
                    )

                    elixir_ok = (
                        resources["elixir"]
                        >= MIN_ATTACK_ELIXIR
                    )

                    dark_elixir_ok = (
                        resources["dark_elixir"]
                        >= MIN_ATTACK_DARK_ELIXIR
                    )

                    print(
                        "Resource test |",
                        "gold_ok =", gold_ok,
                        "| elixir_ok =", elixir_ok,
                        "| dark_elixir_ok =", dark_elixir_ok
                    )

                except Exception as e:
                    print(
                        "Attack resource test failed:",
                        e,
                        "- retrying in 2 seconds"
                    )

                    time.sleep(2.00)
                    continue

                if (
                    gold_ok
                    and elixir_ok
                    and dark_elixir_ok
                ):
                    print("Resources accepted - starting attack")
                    return True

                search_count += 1

                print(
                    "Resources too low - clicking Next |",
                    "search =", search_count,
                    "/",
                    MAX_ATTACK_SEARCHES
                )

                if search_count >= MAX_ATTACK_SEARCHES:
                    print("Maximum opponent searches reached")
                    return False

                # Do not click Next if the preparation time is nearly finished
                if time.time() - start_time > 20:
                    print("Resource check too slow - attacking current base")
                    return True
                
                # Click the Next button
                Input_Handler.click(
                    0.90,
                    0.72
                )

                # Wait for the next opponent to load
                time.sleep(6.00)

                # Restart timeout for the newly loaded opponent
                start_time = time.time()
                continue

            time.sleep(0.1)

        return False
    
    def start_builder_attack(self, timeout=60):
        import time
        
        # Click attack
        Input_Handler.click(0.07, 0.9)
        
        # Find a match
        if not click_with_timeout(
            lambda: Frame_Handler.locate(self.assets["find_now"], thresh=0.9),
            timeout=5
        ): return False
        
        # Wait until "battle starts in" text is found
        start_time = time.time()
        while time.time() - start_time < timeout:
            section = Frame_Handler.get_frame_section(0, 0, 1, 0.1, grayscale=True, high_contrast=True, thresh=150)
            x, y = Frame_Handler.locate(self.assets["battle_starts_in"], section, thresh=0.9)
            if x is not None and y is not None: return True
            time.sleep(0.1)
        return False
    
    def detect_troop_positions(self, frame, clip_left=0.0, clip_right=1.0, type_gaps_seen=0, return_boundaries=False, return_types=False, return_counts=False):
        import cv2, scipy, numpy as np
        
        # Look for vertical card edges
        assert len(frame.shape) == 3 and frame.shape[2] == 3
        frame_color = frame.copy()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        orig_h, orig_w = frame_gray.shape
        frame_color = frame_color[:, max(0, int(orig_w*clip_left)-10):min(orig_w, int(orig_w*clip_right)+10)]
        frame_gray = frame_gray[:, max(0, int(orig_w*clip_left)-10):min(orig_w, int(orig_w*clip_right)+10)]
        frame_gray = cv2.equalizeHist(frame_gray)
        edges = cv2.convertScaleAbs(np.abs(cv2.Sobel(frame_gray, cv2.CV_64F, 1, 0, ksize=3)))
        profile = np.sum(edges, axis=0)
        profile = (profile - profile.min()) / (profile.max() - profile.min())
        peaks = scipy.signal.find_peaks(profile, height=0.8, distance=10)[0]
        peaks_norm =  peaks / orig_w + clip_left
        
        # Compute distances between edges and discretize
        dists = np.diff(peaks_norm)
        dist_categories = np.array([0.007, 0.015, 0.068]) # normal gap, type change gap, card width
        tol = 0.01
        diffs = np.abs(dists[:, None] - dist_categories)
        closest_idx = np.argmin(diffs, axis=1)
        closest_dist = diffs[np.arange(len(dists)), closest_idx]
        dists_discrete = dist_categories[closest_idx]
        dists_discrete[closest_dist > tol] = np.nan
        
        # Remove partially visible card edges
        remove_left = 0
        remove_right = len(dists_discrete) - 1
        while dists_discrete[remove_left] != dist_categories[2]: remove_left += 1
        while dists_discrete[remove_right] != dist_categories[2]: remove_right -= 1
        peaks = peaks[remove_left:remove_right+2]
        peaks_norm = peaks_norm[remove_left:remove_right+2]
        dists_discrete = dists_discrete[remove_left:remove_right+1]
        
        assert len(peaks) % 2 == 0, "Uneven number of troop slot edges detected"
        
        # Convert edge distances to card locations
        card_types = []
        card_centers = []
        card_boundaries = []
        card_counts = []
        for i in range(0, len(peaks_norm), 2):
            x = (peaks_norm[i] + peaks_norm[i+1]) / 2
            card_centers.append(x)
            card_boundaries.extend([peaks_norm[i], peaks_norm[i+1]])
            prev_gap = dists_discrete[i-1] if i-1 > 0 else dist_categories[0]
            next_gap = dists_discrete[i+1] if i+1 < len(dists_discrete) else dist_categories[0]
            if prev_gap == dist_categories[1]: type_gaps_seen += 1
            
            # Figure out whether card is a normal troop, clan troop, or hero
            card_section = frame_color[:, peaks[i]:peaks[i+1]]
            card_section_gray = frame_gray[:, peaks[i]:peaks[i+1]]
            h, w = card_section_gray.shape[:2]
            card_texture = cv2.Canny(card_section_gray, 50, 150) / 255
            x_asset = render_text("x", "SupercellMagic", 25)
            x_h, x_w = x_asset.shape[:2]
            x_sign_loc = Frame_Handler.locate(x_asset, card_section_gray, grayscale=True, thresh=0.75, ref="lc")
            if x_sign_loc[0] is not None and x_sign_loc[1] is not None: # Only troops, clan troops, or spells have multiplicity
                count_section = card_section_gray[:int(h*x_sign_loc[1]+0.5*x_h)+1, int(w*x_sign_loc[0]+x_w)-1:]
                number_locs = Frame_Handler.batch_locate([render_text(str(n), "SupercellMagic", 25) for n in range(0, 12)], frame=count_section, grayscale=True, thresh=0.8, ref="cc")
                
                count = 1
                for i in reversed(range(0, 12)):
                    loc = number_locs[i]
                    if loc[0] is not None and loc[1] is not None:
                        count = i
                        break
                
                # Clan troops either have a clan badge rather than a smooth background
                # or will have wider card edge gaps compared to typical troops
                if max(card_texture[int(h*x_sign_loc[1])-10:int(h*x_sign_loc[1])+10, :int(w*x_sign_loc[0]-1)].mean(1)) > 0.1:
                    card_type = "clan"
                    card_counts.append(1)
                elif prev_gap == dist_categories[1] and next_gap == dist_categories[1]:
                    card_type = "clan"
                    card_counts.append(1)
                elif type_gaps_seen > 0:
                    card_type = "spell"
                    card_counts.append(count)
                else:
                    card_type = "troop"
                    card_counts.append(-1)
            else:
                card_section_border = card_section.copy()
                card_section_border[int(h*0.1):int(h*0.9), int(w*0.1):int(w*0.9)] = 0
                mask = filter_color((68, 202, 222), card_section_border, tol=100, return_mask=True)[1]
                blue_pct = mask.mean()
                # Seige machine doesn't have multiplicity anymore
                if blue_pct > 0.1:
                    card_type = "clan"
                    card_counts.append(1)
                else:
                    card_type = "hero"
                    card_counts.append(1)
            card_types.append(card_type)

        card_centers = np.array(card_centers)
        
        if not return_boundaries and not return_types: return card_centers
        
        output = [card_centers]
        if return_boundaries: output.append(card_boundaries)
        if return_types: output.append(card_types)
        if return_counts: output.append(card_counts)
        output.append(type_gaps_seen)
        return output
    
    def deploy_troops(
        self,
        card_centers,
        available_slots=None,
        card_types=None,
        card_counts=None
    ):
        import time
        import numpy as np

        def card_gray(card_center):
            section = Frame_Handler.get_frame_section(
                card_center - 0.01,
                0.89,
                card_center + 0.01,
                0.91,
                grayscale=False
            )

            return (
                np.all(section[:, :, 0] == section[:, :, 1])
                and np.all(section[:, :, 1] == section[:, :, 2])
            )

        def deploy_on_line(card_center, troop_count, behind=False):
            """
            Purpose:
            Deploy troops one by one using different test coordinates.
            """

            if behind:
                troop_name = "balloon"
                deploy_positions = [
                    (0.48, 0.80),
                    (0.46, 0.80),
                    (0.50, 0.80),
                    (0.44, 0.80),
                    (0.52, 0.80),
                    (0.42, 0.80),
                    (0.54, 0.80),
                    (0.40, 0.80),
                    (0.56, 0.80),
                    (0.44, 0.80),
                    (0.52, 0.80),
                    (0.42, 0.80),
                    (0.54, 0.80),
                ]
            else:
                troop_name = "dragon"
                deploy_positions = [
                    (0.48, 0.80),
                    (0.46, 0.80),
                    (0.50, 0.80),
                    (0.44, 0.80),
                    (0.52, 0.80),
                    (0.42, 0.80),
                    (0.54, 0.80),
                    (0.40, 0.80),
                    (0.56, 0.80),
                    (0.44, 0.80),
                    (0.52, 0.80),
                    (0.42, 0.80),
                    (0.48, 0.80),
                    (0.50, 0.80),                    
                ]

            print("")
            print("========================================")
            print("DEPLOY START")
            print("troop_name =", troop_name)
            print("card_center =", card_center)
            print("troop_count =", troop_count)
            print("========================================")

            Input_Handler.click(card_center, 0.9)
            time.sleep(0.30)

            for click_number in range(1, troop_count + 1):
                current_x, current_y = deploy_positions[
                    click_number - 1
                ]

                # gray_before = card_gray(card_center)

                print(
                    "DEPLOY CLICK |",
                    "troop =", troop_name,
                    "| click =", click_number,
                    "/", troop_count,
                    "| x =", current_x,
                    "| y =", current_y,
                    "| card_center =", card_center
                )

                Input_Handler.click(
                    current_x,
                    current_y
                )

                time.sleep(0.20)

                # gray_after = card_gray(card_center)

                # print(
                #     "DEPLOY RESULT |",
                #     "troop =", troop_name,
                #     "| click =", click_number,
                #     "| x =", current_x,
                #     "| y =", current_y,
                #     "| gray_after =", gray_after
                # )

            print("DEPLOY END =", troop_name)
            print("")

        if available_slots is None:
            available_slots = [1] * len(card_centers)

        if card_types is None:
            card_types = [None] * len(card_centers)

        if card_counts is None:
            card_counts = [0] * len(card_centers)

        # Keeps the troop number between successive calls to deploy_troops()
        if not hasattr(self, "_normal_troop_slot_index"):
            self._normal_troop_slot_index = 0

        for i in range(len(card_centers)):

            if not available_slots[i]:
                continue

            card_center = card_centers[i]
            card_type = card_types[i]

            if card_type == "troop":

                # First troop slot: 12 dragons across the bottom line
                if self._normal_troop_slot_index == 0:
                    print("Deploying 12 dragons")
                    deploy_on_line(
                        card_center=card_center,
                        troop_count=14,
                        behind=False
                    )

                # Second troop slot: 13 balloons slightly behind
                elif self._normal_troop_slot_index == 1:
                    print("Deploying 13 balloons")
                    deploy_on_line(
                        card_center=card_center,
                        troop_count=13,
                        behind=True
                    )

                # Other normal troops: preserve original behavior
                else:
                    Input_Handler.click(card_center, 0.9)
                    time.sleep(0.15)

                    Input_Handler.down(0.5, 0.8, pointer=0)

                    end_time = time.monotonic() + TROOP_DEPLOY_TIME

                    while (
                        time.monotonic() < end_time
                        and not card_gray(card_center)
                    ):
                        time.sleep(0.01)

                    Input_Handler.up(pointer=0)

                self._normal_troop_slot_index += 1

            elif card_type in ["hero", "clan"]:

                Input_Handler.click(card_center, 0.9)
                time.sleep(0.15)
                Input_Handler.click(0.5, 0.8)

            elif card_type == "spell":

                Input_Handler.click(card_center, 0.9)
                time.sleep(0.15)

                n = card_counts[i]
                rxs = np.random.uniform(0.35, 0.65, n)
                rys = np.random.uniform(0.45, 0.55, n)

                for coord in zip(rxs, rys):
                    Input_Handler.click(*coord)
                    time.sleep(0.10)

            else:

                Input_Handler.click(card_center, 0.9)
                time.sleep(0.15)

                Input_Handler.click(
                    0.5,
                    0.8,
                    n=max(0, card_counts[i])
                )

        # Unselect the final card
        Input_Handler.click(0.01, 0.9)
    
    def complete_normal_attack(self, restart=True, exclude_clan_troops=False):
        import time, numpy as np
        
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_up()

        # Purpose: Restart troop slot numbering for every new attack
        self._normal_troop_slot_index = 0
        
        type_gaps_seen = 0
        total_slots_seen = 0
        last_card_left = 0.0
        
        while total_slots_seen < ATTACK_SLOT_RANGE[1] - ATTACK_SLOT_RANGE[0] + 1:
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            # Find troops to deploy
            card_centers, card_boundaries, card_types, card_counts, type_gaps_seen = self.detect_troop_positions(frame, clip_left=last_card_left, type_gaps_seen=type_gaps_seen, return_boundaries=True, return_types=True, return_counts=True)
            
            if len(card_centers) == 0: break

            # Exclude clan troops if specified
            available_slots = np.ones_like(card_centers)
            if exclude_clan_troops:
                for i, card_type in enumerate(card_types):
                    if card_type == "clan": available_slots[i] = 0
            
            # Exclude troops outside of specified slot range
            available_slots[:max(0, ATTACK_SLOT_RANGE[0] - total_slots_seen)] = 0
            available_slots[max(0, ATTACK_SLOT_RANGE[1] + 1 - total_slots_seen):] = 0
            
            # Deploy troops up until the last one visible
            total_slots_seen += len(card_centers) - 1
            self.deploy_troops(card_centers[:-1], available_slots[:-1], card_types[:-1], card_counts[:-1])
            # Scroll over and look for the new position of the last card
            last_card_frame = frame[:, int(card_boundaries[-2] * frame.shape[1]):int(card_boundaries[-1] * frame.shape[1])]
            Input_Handler.swipe_left(x1=card_centers[-1], x2=0.038, y=0.9, hold_end_time=500)
            time.sleep(0.5)
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            last_card_left = Frame_Handler.locate(last_card_frame, frame, thresh=0.9, grayscale=False, ref="lc")[0]
            # If the card didn't move then there are no more troops so it can be deployed
            if last_card_left is not None and abs(last_card_left - card_boundaries[-2]) < 0.01:
                self.deploy_troops(card_centers[-1:], available_slots[-1:], card_types[-1:], card_counts[-1:])
                break
            elif last_card_left is None:
                break
        
        # Close and reopen CoC to auto complete battle
        #if restart:
        #    start_coc()
        #else:
        #    stop_coc()
        #ADD BY GBO 10 juil. 2026 03:30 PM
        print("Skipping CoC restart/stop after attack")
    
    def complete_builder_attack(self, restart=True):
        import numpy as np
        
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_up()
        
        card_centers = np.linspace(0.1, 0.9, 11)
        self.deploy_troops(card_centers, card_counts=[4]*len(card_centers))
        
        # Close and reopen CoC to auto complete battle
        # if restart:
        #     start_coc()
        # else:
        #     stop_coc()
        print("Skipping CoC restart/stop after attack")
    
    # ============================================================
    # ⚔️ Attack Management
    # ============================================================

    @require_exit()
    def run_home_base(self, timeout=60, restart=True):
        import time
        
        try:
            print("### RUN HOME BASE STARTED ###")

            # Make sure in home base
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    get_home_builders(1)
                    print("### HOME BASE DETECTED ###")
                    break

                except (KeyboardInterrupt, SystemExit):
                    raise

                except Exception as e:
                    print("Home base detection failed:", e)
                    time.sleep(1.00)

            if time.time() - start_time >= timeout:
                print("### HOME BASE DETECTION TIMEOUT ###")
                return

            # print("### CALLING REINFORCEMENT CHECK ###")
            # self.request_free_reinforcements()
            
            # Complete an attack
            if self.start_normal_attack(timeout):
                self.complete_normal_attack(
                    restart=restart,
                    exclude_clan_troops=EXCLUDE_CLAN_TROOPS
                )
        
        except Exception as e:
            if configs.DEBUG: print("attack_home_base", e)

    @require_exit()
    def run_builder_base(self, timeout=60, restart=True):
        import time
        
        try:
            # Make sure in builder base
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    get_builder_builders(1)
                    break
                except (KeyboardInterrupt, SystemExit): raise
                except: pass
            if time.time() - start_time >= timeout: return
            
            # Complete an attack
            if self.start_builder_attack(timeout):
                self.complete_builder_attack(restart=restart)
        
        except Exception as e:
            if configs.DEBUG: print("attack_builder_base", e)
