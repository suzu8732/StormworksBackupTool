import json
import os
import datetime as dt
import shutil
import glob

def get_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print('configファイルが存在しません')
        raise
    
    return config

def get_backup_history(output_path):
    try:
        with open(f'{output_path}/history.json', 'r') as f:
            history = json.load(f)
            if 'last_backup_date' in history:
                last_backup_date = dt.datetime.strptime(history['last_backup_date'], '%Y-%m-%d').date()
            else:
                last_backup_date = dt.date.today() - dt.timedelta(days=1)
            last_full_backup_date = dt.datetime.strptime(history['last_full_backup_date'], '%Y-%m-%d').date()
            return last_backup_date, last_full_backup_date
    except FileNotFoundError:
        print('historyファイルが存在しません(フルバックアップが実行されます)')
        return None, None

def determine_backup_mode(date, config, last_full_backup_date):
    if last_full_backup_date != None:
        full_backup_elapsed_days = (date - last_full_backup_date).days
        full_backup_interval = config['full_backup_interval']
        return full_backup_elapsed_days >= full_backup_interval
    else:
        return True

def copy_game_directory(game_data_path, target_dir_name, output_path, is_full, last_full_buckup):
    if is_full:
        shutil.copytree(f'{game_data_path}/{target_dir_name}', f'{output_path}/{target_dir_name}')
        pass
    else:
        for f in glob.iglob(f'{game_data_path}/{target_dir_name}/**/', recursive = True):
            os.makedirs(output_path + f[len(game_data_path):], exist_ok = True)
        for f in glob.iglob(f'{game_data_path}/{target_dir_name}/**/*', recursive = True):
            if os.path.isfile(f):
                last_update_date = dt.datetime.fromtimestamp(os.path.getmtime(f)).date()
                if last_update_date > last_full_buckup:
                    shutil.copy2(f, f'{output_path}/{f.split(f'/data/')[1]}')
            

def buckup_directory(date, config, is_full, last_full_backup_date):
    game_data_dir = os.getenv('APPDATA').replace('\\', '/') + '/Stormworks/data'
    date_dir_name = date.strftime('%Y-%m-%d')
    output_path = f'{config['output_path']}/{date_dir_name}'
    
    os.makedirs(output_path, exist_ok=True)
    for target_name in config['target_directory']:
        copy_game_directory(game_data_dir, target_name, output_path, is_full, last_full_backup_date)
    
    additional_dirs = config['additional_backup_directory']
    for dir in additional_dirs:
        dir_path = f'{output_path}/追加ディレクトリ/{dir['name']}'
        os.makedirs(dir_path, exist_ok = True)
        shutil.copytree(dir['path'], dir_path, dirs_exist_ok=True)

def main():
    config = get_config()
    output_path = config['output_path']
    today = dt.date.today()

    last_backup_date, last_full_backup_date = get_backup_history(output_path)
    if last_backup_date != None and (today - last_backup_date).days <= 0:
        print('バックアップがスキップされました')
        return

    is_full = determine_backup_mode(today, config, last_full_backup_date)
    buckup_directory(today, config, is_full, last_full_backup_date)

    today_str = today.strftime('%Y-%m-%d')
    if is_full:
        last_full_backup_date = today
        print('バックアップ完了(種類： フル)')
    else:
        print('バックアップ完了(種類： 差分のみ)')

    with open(f'{output_path}/history.json', 'w') as f:
        backup_history = {}
        backup_history['last_backup_date'] = today_str
        backup_history['last_full_backup_date'] = last_full_backup_date.strftime('%Y-%m-%d')
        json.dump(backup_history, f, indent=4)

if __name__ == '__main__':
    main()