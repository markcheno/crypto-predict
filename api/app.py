"""Run the API by calling this module"""
import connexion
import logging
from flask import abort
import pandas as pd
from crypr.models import SavedKerasTensorflowModel
from crypr.preprocessors import DWTSmoothPreprocessor
from crypr.cryptocompare import retrieve_all_data
from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())
base_path = os.path.dirname(find_dotenv())

model_type = 'ae_lstm'
wavelet = 'haar'

global btc_model, eth_model
btc_model = SavedKerasTensorflowModel('{}/models/{}_smooth_{}x{}_{}_{}.h5'.format(base_path, model_type, 1, 72, wavelet, 'BTC'))
eth_model = SavedKerasTensorflowModel('{}/models/{}_smooth_{}x{}_{}_{}.h5'.format(base_path, model_type, 1, 72, wavelet, 'ETH'))


def description():
    return {'message': 'The crypto-predict API'}


def say_hello(name=None):
    return {'message': 'Hello, {}!'.format(name or '')}


def predict(coin=None):
    coin = coin or 'BTC'
    wavelet = 'haar'
    Tx = 72
    Ty = 1
    target = 'close'

    cryptocompare_data = retrieve_all_data(coin, Tx + 1)

    preprocessor = DWTSmoothPreprocessor(
        production=True,
        target_col=target,
        Tx=Tx,
        Ty=Ty,
        wavelet=wavelet,
        name='CryptoPredict_DWTSmoothPreprocessor_{}'.format(coin))
    preprocessed_data = preprocessor.fit(cryptocompare_data).transform(cryptocompare_data)

    if coin == 'ETH':
        model = eth_model
    elif coin == 'BTC':
        model = btc_model
    else:
        #FIXME: More descriptive error
        abort(404)
    with model.graph.as_default():
        prediction = model.estimator.predict(preprocessed_data)

    def parse_keras_prediction(keras_prediction):
        """Handles multi-output Keras models"""
        if len(keras_prediction) == 2:
            return keras_prediction[1][0]
        else:
            return keras_prediction[0]
    parsed_prediction = parse_keras_prediction(prediction)

    last_value = cryptocompare_data[target].iloc[-1]
    last_time = cryptocompare_data['timestamp'].iloc[-1]

    prediction_val = [last_value + pred / 100 * last_value for pred in parsed_prediction]
    time_val = [last_time + pd.Timedelta(hours=1 * (int(ix) + 1)) for ix in range(len(parsed_prediction))]
    return dict(prediction=prediction_val, time=time_val)


logging.basicConfig(level=logging.DEBUG)
app = connexion.App(__name__)
app.add_api('swagger.yaml')
application = app.app


if __name__ == '__main__':
    app.run(port=5000, server='gevent')
