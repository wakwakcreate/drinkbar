import pandas as pd

scripts = {}

def load_scripts():
    # お題の選択肢
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/scenario.csv"
    scenarios_csv = pd.read_csv(url)
    scenarios = []
    for _, row in scenarios_csv.iterrows():
        answers = [row['ans0'], row['ans1'], row['ans2']]
        scenario = {
            'question': row['question'],
            'answers': answers,
        }
        scenarios.append(scenario)
    scripts['scenarios'] = scenarios

    # 個別に送るメッセージ
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/mission.csv"
    missions_csv = pd.read_csv(url)
    missions = []
    for _, row in missions_csv.iterrows():
        missions.append(row['mission'])
    scripts['missions'] = missions

    # ヘンテコミッション（easy, hard）
    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/easymission.csv"
    easy_missions_csv = pd.read_csv(url)
    easy_missions = []
    for _, row in easy_missions_csv.iterrows():
        easy_missions.append(row['mission'])
    scripts['easy_missions'] = easy_missions

    url = "https://raw.githubusercontent.com/wakwakcreate/drink_scripts/main/hardmission.csv"
    hard_missions_csv = pd.read_csv(url)
    hard_missions = []
    for _, row in hard_missions_csv.iterrows():
        hard_missions.append(row['mission'])
    scripts['hard_missions'] = hard_missions

    print("Scripts loaded.")

# TODO: Make it more complicated
dummy_scripts = {
    'scenarios': [
        {'question': 'q0', 'answers': ['a00', 'a01', 'a02']},
        {'question': 'q1', 'answers': ['a10', 'a11', 'a12']},
        {'question': 'q2', 'answers': ['a20', 'a21', 'a22']},
        {'question': 'q3', 'answers': ['a30', 'a31', 'a32']},
        {'question': 'q4', 'answers': ['a40', 'a41', 'a42']},
    ],
    'missions': [
        'Missions for melon',
        'Missions for orange',
        'Missions for oolong',
        'Missions for jasmine',
    ],
    'easy_missions': [
        'Easy mission 0',
        'Easy mission 1',
        'Easy mission 2',
        'Easy mission 3',
        'Easy mission 4',
    ],
    'hard_missions': [
        'Hard mission 0',
        'Hard mission 1',
        'Hard mission 2',
        'Hard mission 3',
        'Hard mission 4',
    ]
}