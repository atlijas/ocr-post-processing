from pathlib import Path
import argparse
import pandas
from utils.sql.db_setup import FileToSQL
from utils.error_files_setup import write_replacements_to_single_file, create_correct_word_list
from globals import (read_files,
                     tokenize,
                     ORIGINAL_FILES,
                     CORRECTED_FILES,
                     ORIGINAL_VAL_FILES,
                     CORRECTED_VAL_FILES,
                     TOKENIZER_INFO)
from train import SRC_LANGUAGE, TGT_LANGUAGE
from ocr_dataset import OCRDataset


parser = argparse.ArgumentParser()
parser.add_argument('--type', help='What to set up, error files or dataframes')
args = parser.parse_args()

def handle_file(filename):
    file_path = Path(filename)
    if file_path.is_file():
        print(f'> {Path(filename).name} already exists. Overwriting.')
        file_path.unlink()
    else:
        print(f'> Writing to {Path(filename).name}.')



if __name__ == '__main__':
    if args.type == 'dataframes':
        print('> Building training dataframe')
        training_data = pandas.DataFrame()
        training_data['original'] = list(read_files(ORIGINAL_FILES, tokenizer=tokenize))
        training_data['corrected'] = list(read_files(CORRECTED_FILES, tokenizer=tokenize))
        TRAINING_DATASET = OCRDataset(df=training_data, source_column=SRC_LANGUAGE, target_column=TGT_LANGUAGE)
        torch.save(training_data(TRAINING_DATASET.source_vocab), 'dataframes/train_src_vocab.pth')
        torch.save(training_data(TRAINING_DATASET.target_vocab), 'dataframes/train_tgt_vocab.pth')
        training_data.to_pickle(f'dataframes/training_data_{TOKENIZER_INFO}.pickle')

        print('> Building validation dataframe')
        validation_data = pandas.DataFrame()
        validation_data['original'] = list(read_files(ORIGINAL_VAL_FILES, tokenizer=tokenize))
        validation_data['corrected'] = list(read_files(CORRECTED_VAL_FILES, tokenizer=tokenize))
        VALIDATION_DATASET = OCRDataset(df=VALIDATION_DATA, source_column=SRC_LANGUAGE, target_column=TGT_LANGUAGE)
        torch.save(validation_data(VALIDATION_DATASET.source_vocab), 'dataframes/val_src_vocab.pth')
        torch.save(validation_data(VALIDATION_DATASET.target_vocab), 'dataframes/val_tgt_vocab.pth')
        validation_data.to_pickle(f'dataframes/validation_data_{TOKENIZER_INFO}.pickle')

    elif args.type == 'errors':
        correct_words = create_correct_word_list(f'data/parallel/60k_gold/corrected/')
        print('> Setting up files...')
        write_replacements_to_single_file('data/errors/all_replacements.tsv',
                                          correct_word_list=correct_words,
                                          ocr_files_path='data/parallel/60k_gold/original',
                                          corrected_files_path='data/parallel/60k_gold/corrected')
        print('> Setting up databases...')
        # This database contains original_string, corrected_string, frequency_of_substitution
        handle_file('dbs/replacements.db')
        original_replacement_to_db = FileToSQL(file_to_db='data/errors/all_replacements.tsv',
                                               db_name='dbs/replacements')
        original_replacement_to_db.create_db_orig_corr_freq('REPLACEMENTS',
                                                            'original',
                                                            'replacement',
                                                            'frequency',
                                                            field_separator='\t',
                                                            headers=['original',
                                                                     'replacement',
                                                                     'frequency'])
    else:
        parser.error('Argument missing.')
