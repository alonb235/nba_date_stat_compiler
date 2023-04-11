"""
author: Alon Baruch (alonb235@gmail.com)

This script sets up web server and request handler

server accepts get commands with date, request handler makes commands to API_NBA
https://rapidapi.com/api-sports/api/api-nba

"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import requests


class RequestHandler(BaseHTTPRequestHandler):
    """
        Expects Get Requests with dates in path,
        makes calls to API_NBA and decodes response and formats 
        response text
    """
    def do_POST(self):
        self.send_response(400, "Invalid Request")
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        status_code, message = self.get_date_stats(self.path)

        # validate request
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # format responses
        self.wfile.write(bytes(message, "utf8"))

    def get_date_stats(self, path):
        headers = {
            "X-RapidAPI-Key": "<INSERT API KEY HERE>",
            "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
        }

        # removes / from path
        date = path[1:]

        # get games played on date
        querystring = {"date":date}
        url = "https://api-nba-v1.p.rapidapi.com/games"
        response = requests.request("GET", url, headers=headers, params=querystring)

        if response.status_code == 200:
            game_dict = response.json()
            status_code, message = self.format_games_response(game_dict, date)
            return status_code, message
        else:
            return response.status_code, response.text
    
    def format_games_response(self, games_json, date):
        """
            Takes in json object representing games
            returns dictionary with game id as the key 
            and a tuple with home team, visitor team, and scores as the value
            {game id: (home, visitor, (home score, visitor score))}
        """
        if games_json['errors'] != []:
            return 400, str(games_json['errors'])
        
        if games_json['results'] > 0:
            game_str, game_ids = self.game_results(games_json)
            stat_leaders = self.stat_leaders(game_ids)
            # save game ids to calculate stat leaders
            
            message = "Games Played on {d}:\n{g_str} \nStat Leaders on {d}: \n{s_str}".format(d=date, g_str=game_str, s_str=stat_leaders)
        else:
            message = "No Games played on {}".format(date)

        return 200, message

    def game_results(self, games_json):
        game_results = []
        game_ids = []
        for i in games_json['response']:
            game_ids.append(i['id'])
            visitor_score = i['scores']['visitors']['points']
            home_score = i['scores']['home']['points']
            visitor=i['teams']['visitors']['code']
            home=i['teams']['home']['code']

            if visitor_score > home_score:
                result = "{v} {v_score} @ {h_score} {h}".format(v=visitor, 
                                                                    v_score=visitor_score,
                                                                    h=home,
                                                                    h_score=home_score)
            else:
                result = "{h} {h_score} vs {v_score} {v}".format(h=home,
                                                                    h_score=home_score,
                                                                    v=visitor, 
                                                                    v_score=visitor_score)
                
            game_results.append(result)
        
        game_string = "\n".join(map(str, game_results))
                
        #compile game results
        return game_string, game_ids
    
    def stat_leaders(self, game_ids):
        pnt_leaders, ast_leaders, reb_leaders, stl_leaders, blk_leaders = {}, {}, {}, {}, {}

        # iterate through game ids
        for i in game_ids:
            url = "https://api-nba-v1.p.rapidapi.com/players/statistics"
            querystring = {"game":i}
            headers = {
                "X-RapidAPI-Key": "<INSEPT API KEY HERE>",
                "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
            }
            response = requests.request("GET", url, headers=headers, params=querystring)
            game_stats = response.json()

            pnt_lead, ast_lead, reb_lead, stl_lead, blk_lead = self.get_game_leaders(game_stats)
            
            pnt_leaders.update(pnt_lead)
            ast_leaders.update(ast_lead)
            reb_leaders.update(reb_lead)
            stl_leaders.update(stl_lead)
            blk_leaders.update(blk_lead)

        date_pnt_leader = max(pnt_leaders, key=pnt_leaders.get)
        date_ast_leader = max(ast_leaders, key=ast_leaders.get)
        date_reb_leader = max(reb_leaders, key=reb_leaders.get)
        date_stl_leader = max(stl_leaders, key=stl_leaders.get)
        date_blk_leader = max(blk_leaders, key=blk_leaders.get)

        stat_leader_message = "Points: {p_name} ({p})\nAssits: {a_name} ({a})\nRebounds: {r_name} ({r})\nSteals: {s_name} ({s})\nBlocks: {b_name} ({b})".format(
            p_name = date_pnt_leader, p=pnt_leaders[date_pnt_leader],
            a_name = date_ast_leader, a=ast_leaders[date_ast_leader],
            r_name = date_reb_leader, r=reb_leaders[date_reb_leader],
            s_name = date_stl_leader, s=stl_leaders[date_stl_leader],
            b_name = date_blk_leader, b=blk_leaders[date_blk_leader]
        )

        return stat_leader_message

    def get_game_leaders(self, game_stats):
        max_pnt, max_ast, max_reb, max_stl, max_blk = 0, 0, 0, 0, 0
        pnt_play, ast_play, reb_play, stl_play, blk_play = "", "", "", "", ""

        for i in game_stats['response']:
            if i['points'] != None and i['points'] > max_pnt:
                max_pnt = i['points']
                pnt_play = "{} {}".format(i['player']['firstname'], i['player']['lastname'])
            if i['assists'] != None and i['assists'] > max_ast:
                max_ast = i['assists']
                ast_play = "{} {}".format(i['player']['firstname'], i['player']['lastname'])
            if i['totReb'] != None and i['totReb'] > max_reb:
                max_reb = i['totReb']
                reb_play = "{} {}".format(i['player']['firstname'], i['player']['lastname'])
            if i['steals'] != None and i['steals'] > max_stl:
                max_stl = i['steals']
                stl_play = "{} {}".format(i['player']['firstname'], i['player']['lastname'])
            if i['blocks'] != None and i['blocks'] > max_blk:
                max_blk = i['blocks']
                blk_play = "{} {}".format(i['player']['firstname'], i['player']['lastname'])

        return {pnt_play: max_pnt}, {ast_play: max_ast}, {reb_play: max_reb}, {stl_play: max_stl}, {blk_play: max_blk}


class NBAStatServer:
    """
        *ADD DESCRIPTION OF SERVER CLASS*
    """
    def __init__(self) -> None:
        server_address = ('', 8080)
        self.httpd = HTTPServer(server_address, RequestHandler)

    def run(self):
        self.httpd.serve_forever()
