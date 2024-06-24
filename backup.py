import json
import os
import datetime as dt
import shutil
import glob

def get_config() -> dict:
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print('configファイルが存在しません')
        raise
    
    return config

def get_last_full_backup(output_path: str) -> dt.date:
    try:
        with open(f'{output_path}/history.json', 'r') as f:
            history = json.load(f)
            date: str = history['last_full_backup_date']
            return dt.datetime.strptime(date, '%Y-%m-%d').date()
    except FileNotFoundError:
        print('historyファイルが存在しません(フルバックアップが実行されます)')
        return None

def determine_backup_mode(date: dt.date, config: dict, last_full_backup: dt.date):
    if last_full_backup != None:
        full_backup_elapsed_days = (date - last_full_backup).days
        full_backup_interval = config['full_backup_interval']
        return full_backup_elapsed_days >= full_backup_interval
    else:
        return True

def copy_game_directory(game_data_path: str, target_dir_name: str, output_path: str, is_full: bool, last_full_buckup: dt.date):
    if is_full:
        shutil.copytree(f'{game_data_path}/{target_dir_name}', f'{output_path}/{target_dir_name}')
        pass
    else:
        for f in glob.iglob(f'{game_data_path}/{target_dir_name}/**/', recursive=True):
            os.makedirs(output_path + f[len(game_data_path):], exist_ok=True)
        for f in glob.iglob(f'{game_data_path}/{target_dir_name}/**/*', recursive=True):
            if os.path.isfile(f):
                last_update_date = dt.datetime.fromtimestamp(os.path.getmtime(f)).date()
                if last_update_date > last_full_buckup:
                    shutil.copy2(f, f'{output_path}/{f.split(f'/data/')[1]}')
            

def buckup_directory(date: dt.date, config: dict, is_full: bool, last_full_backup: dt.date):
    game_data_dir = os.getenv('APPDATA').replace('\\', '/') + '/Stormworks/data'
    date_dir_name = date.strftime('%Y-%m-%d')
    output_path = f'{config['output_path']}/{date_dir_name}'
    
    os.makedirs(output_path, exist_ok=True)
    for target_name in config['target_directory']:
        copy_game_directory(game_data_dir, target_name, output_path, is_full, last_full_backup)
    
    additional_dirs: list = config['additional_backup_directory']
    for dir in additional_dirs:
        dir_path = f'{output_path}/追加ディレクトリ/{dir['name']}'
        os.makedirs(dir_path)
        shutil.copytree(dir['path'], dir_path, dirs_exist_ok=True)

def main():
    config = get_config()
    output_path = config['output_path']
    today = dt.datetime.now().date()

    last_full_backup = get_last_full_backup(output_path)
    is_full = determine_backup_mode(today, config, last_full_backup)
    
    buckup_directory(today, config, is_full, last_full_backup)

    if is_full:
        backup_history = {}
        backup_history['last_full_backup_date'] = today.strftime('%Y-%m-%d')
        with open(f'{output_path}/history.json', 'w') as f:
            json.dump(backup_history, f, indent=4)
        print('バックアップ完了(種類： フル)')
    else:
        print('バックアップ完了(種類： 差分のみ)')

if __name__ == '__main__':
    main()