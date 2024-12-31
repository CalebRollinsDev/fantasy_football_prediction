import streamlit as st
from pydantic import BaseModel
import pandas as pd


metric_columns = [
    'linear predicted points',
    'boosting predicted points',
    'neighbors predicted points',
    'linear Prob > 10',
    'boosting Prob > 10',
    'neighbors Prob > 10',
    'linear Prob > 15',
    'boosting Prob > 15',
    'neighbors Prob > 15',
    'linear Prob > 20',
    'boosting Prob > 20',
    'neighbors Prob > 20'
]


INTRO = '''
These are predictions for draftkings scores which is PPR. Under "Models to Show", 
there are entries for different models. Linear, boosting, and neighbors are different
model types. Boosting is the best of the three with linear a close second. Predicted points
is the predicted number of fantasy points the player will score. Prob > N is the probability
the player will score more than N points. You can click on a column name to sort by that 
column.
'''

def setup_df(df, current):
    
    new_df = df.copy()

    def get_position(row):
        if row['is Quarterbacks']:
            return 'QB'
        if row['is Running Backs']:
            return 'RB'
        if row['is Tight Ends']:
            return 'TE'
        if row['is Wide Receivers']:
            return 'WR'
    new_df['Position'] = [get_position(row) for _, row in new_df.iterrows()]
    if current:
        new_df['Name'] = new_df['player_id']
    else:
        new_df['Name'] = new_df['player_id'].apply(lambda x: x[:-3])
    new_df['salary'] = new_df['salary'] * 100
    return new_df

def get_filtered_df(df, week=None, position=None, column_filters=None, models=None, actual: bool = True):
    models = models or []
    query = '(Week > 0)'
    actual = ['actual'] if actual else []
    cols = ['Name', 'Position', 'Week', 'salary',] + actual + models
    if week is not None:
        query += ' and (Week == {})'.format(week)
    if position is not None:
        query += ' and (Position == "{}")'.format(position)
    if column_filters is not None:
        for col, gt_or_lt, val in column_filters:
            query += ' and ({} {} {})'.format(col, gt_or_lt, val)
    print(query)
    return df.query(query).loc[:, cols]

if 'pred_df' not in st.session_state:
    st.session_state['pred_df'] = setup_df(pd.read_csv('full_fantasy_predictions_2020'), False) 

if 'current_df' not in st.session_state:
    st.session_state['current_df'] = setup_df(pd.read_csv('full_fantasy_predictions_2024_with_week_17'), True) 
    # st.session_state['current_df']['actual'] = 0

class PredictionDashboard(BaseModel):
    mobile: bool = False
    current: bool = True
    with_intro: bool = False

    
    def pred_df(self, current: bool) -> pd.DataFrame:
        if current:
            return st.session_state['current_df']
        else:
            return st.session_state['pred_df']
    
    def run_dashboard(self):
        if self.with_intro:
            st.write(INTRO)
        models = st.multiselect('Models to Show', metric_columns, default=['boosting predicted points'])
        if not self.current:
            week = st.selectbox('Week', ['2024 Week 17'] + [f'2020 Week {i}' for i in range(5, 18)])
            if '2024' in week:
                week = None
                current = True
            else:
                week = int(week.split(' ')[2])
                current = False
        else:
            week = None
        position = st.selectbox(
            'Position', ['QB', 'RB', 'WR', 'TE']
        )
        df = get_filtered_df(
            self.pred_df(current=current),
            week=week,
            position=position,
            models=models,
            actual=True
        ).copy()
        df.index = df['Name']
        df = df.drop('Name', axis=1)
        
        st.dataframe(df, use_container_width=True)

if __name__ == '__main__':
    PredictionDashboard(current=False).run_dashboard()
