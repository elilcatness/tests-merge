import os
from lxml import html


def get_doc(filename: str):
    with open(filename, encoding='utf-8') as f:
        return html.fromstring(f.read().strip())


def main(folder: str = 'tests', output_filename: str = 'tests.txt'):
    filenames = os.listdir(folder)
    if not filenames:
        raise Exception('Trials folder is empty')
    data = dict()
    for i, filename in enumerate(filenames, 1):
        doc = get_doc(os.path.join(folder, filename))
        if doc is None:
            raise Exception(f'Fatal error on loading {filename}')
        cards = doc.xpath('//div[@class="que multichoice deferredfeedback complete"]')
        if not cards:
            raise Exception(f'Found no cards on {filename}')
        for j, card in enumerate(cards, 1):
            try:
                question = card.xpath('.//div[@class="qtext"]')[0].text_content().strip()
                assert question
            except (IndexError, AssertionError):
                raise Exception(f'Failed to get question on {filename} [card #{j}]')
            if question in data:
                print(f'[{filename}, card #{j}] Skip due not unique question')
                continue
            try:
                grade = card.xpath('.//div[@class="grade"]')[0].text_content().strip()
                assert grade
            except (IndexError, AssertionError):
                raise Exception(f'Failed to get grade of answer on {filename} [card #{j}]')
            score, max_score = [float(_score.strip()) for _score 
                                in grade.split(':')[1].strip().split('из')]
            to_be_skipped = score == 0
            prev_question = None
            if score < max_score:
                prev_question = question
                question = f'({score}) {question}'
            answers = (card.xpath('.//div[@class="answer"]//div[@class="r0"]') + 
                       card.xpath('.//div[@class="answer"]//div[@class="r1"]'))
            correct_answers = []
            all_answers = []
            for ans in answers:
                try:
                    ans_text = ans.xpath('.//div[@class="flex-fill ml-1"]')[0].text_content().strip()
                    # ans_text = ans_text.encode('utf-8').decode('windows-1251')
                    assert ans_text
                except (IndexError, AssertionError):
                    raise Exception('[{filename}] Failed to read ans text on card #{j}')
                try:
                    all_answers.append(ans_text.lower())
                    if ans.xpath('./input/@checked')[0] != 'checked':
                        continue
                except IndexError:
                    continue
                try:
                    ans_num = ans.xpath('.//span[@class="answernumber"]')[0].text_content().strip()
                    assert ans_num
                except (IndexError, AssertionError):
                    raise Exception('[{filename}] Failed to read ans num on card #{j}')
                correct_answers.append(f'{ans_num} {ans_text}')
            choices = ['вeрнo', 'нeвeрнo']
            if (all(_ans.lower() in choices for _ans in all_answers) and to_be_skipped 
                and len(correct_answers) == 1 and correct_answers[0].lower().split('. ')[1] in choices):
                ans_num, ans_text = correct_answers[0].lower().split('. ')
                ch = 'Верно' if ans_text == 'неверно' else 'Неверно'
                correct_answers[0] = f'{ans_num}. {ch}'
                if prev_question:
                    question = prev_question
                to_be_skipped = False
            if not to_be_skipped:
                # question = f'{filename}. {question}'
                data[question] = sorted(correct_answers, key=lambda x: int(x.split('.')[0]))
            else:
                print(f'[{filename}, card #{j}] Skip due unequal scores: {score} from {max_score}')
    s = ''
    i = 0
    for question, answers in data.items():
        i += 1
        s0 = f'Q{i}: {question}\n' + '\n'.join(answers) + '\n\n'
        s += s0
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(s)


if __name__ == '__main__':
    main()