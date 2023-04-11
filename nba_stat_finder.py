"""
author: Alon Baruch (alonb235@gmail.com)

This script handles user input

users can input dates and gets returned, games played and results, and stat leaders for that day

usage: ./nba_stat_finder.py [date]
"""
import requests
import argparse
from dateutil.parser import parse
from server import NBAStatServer
import threading

def validate_date(date):
    """
        Uses python dateutil parse method to convert string to valid date format
    """
    try:
        valid_date = parse(date)
        return str(valid_date)[:10]
    except ValueError:
        print("Invalid date")
        return None

def call_requests(date):
    """
        Makes request to local web service to get states for given date
    """
    response = requests.get("http://localhost:8080/{}".format(date))

    # check response status
    if response.status_code == 200:
        print(response.text)
    elif response.status_code == 400:
        print("Invalid Request")
    elif response.status_code == 500:
        print("Unkown Error")


if __name__ == '__main__':
    # initialize web servers
    server = NBAStatServer()
    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()

    parser = argparse.ArgumentParser(prog='NBAStatFinder',description='Returns answer to users query')
    parser.add_argument('--date', '-d', type=str, required=True, help='Required Input: Date for stats query')
    args = parser.parse_args()

    # checks date inputted
    valid_date = validate_date(args.date)

    # makes sure date is valid before making call
    if valid_date != None:
        call_requests(valid_date)
