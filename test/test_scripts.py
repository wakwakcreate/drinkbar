from ..src.scripts import load_scripts, scripts

def test_load_scripts():
    # Load check
    load_scripts()

    # Key check
    assert('scenarios' in scripts)
    assert('missions' in scripts)
    assert('easy_missions' in scripts)
    assert('hard_missions' in scripts)

    # Data check
    scenarios = scripts['scenarios']
    assert(len(scenarios) > 0)
    for row in scenarios:
        assert('question' in row)
        assert(isinstance(row['question'], str))

        assert('answers' in row)
        answers = row['answers']
        assert(len(answers) == 3)
        for answer in answers:
            assert(isinstance(answer, str))
    
    missions = scripts['missions']
    assert(len(missions) == 4)
    for mission in missions:
        assert(isinstance(mission, str))
    
    easy_missions = scripts['easy_missions']
    assert(len(easy_missions) > 0)
    for mission in easy_missions:
        assert(isinstance(mission, str))
    
    hard_missions = scripts['hard_missions']
    assert(len(hard_missions) > 0)
    for mission in hard_missions:
        assert(isinstance(mission, str))

    
