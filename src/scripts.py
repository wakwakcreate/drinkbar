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

dummy_scripts = {
    'scenarios': [
        {'question': 'q0', 'answers': ['a0', 'a1', 'a2']}
    ],
    'missions': [
        'Missions for melon',
        'Missions for orange',
        'Missions for oolong',
        'Missions for jasmine',
    ],
    'easy_missions': [
        'Easy mission 0'
    ],
    'hard_missions': [
        'Hard mission 0'
    ]
}