import sys

sys.path.append('..')

from core.nnet.NNetTPU import NNetTPU

from tensorflow.python import keras

from tensorflow.python.keras.models import *
from tensorflow.python.keras.layers import *
from tensorflow.python.keras.optimizers import *

from tensorflow.python.keras.layers import Input
from tensorflow.python.keras.models import Model
from tensorflow.python.keras.losses import mean_squared_error
from tensorflow.python.keras.regularizers import l2

from tensorflow.python.keras.utils import multi_gpu_model as make_multi_gpu


class CheckersResNNetTPU(NNetTPU):
    learning_rate = 0.001

    cnn_filter_num = 256
    cnn_first_filter_size = 5
    cnn_filter_size = 3
    res_layer_num = 7
    l2_reg = 1e-4
    value_fc_size = 256

    def build_model(self):

        input_boards = Input(
            shape=(self.observation_size_x, self.observation_size_y, self.observation_size_z),
            name=self._INPUT_NODE_UNIQUE_IDENTIFIER[0])  # s: batch_size x board_x x board_y

        x = Reshape((self.observation_size_x, self.observation_size_y, self.observation_size_z))(
            input_boards)  # batch_size  x board_x x board_y x 1

        # (batch, channels, height, width)
        x = Conv2D(filters=self.cnn_filter_num, kernel_size=self.cnn_first_filter_size,
                   padding="same",
                   data_format="channels_first", use_bias=False, kernel_regularizer=l2(self.l2_reg),
                   name="input_conv-" + str(self.cnn_first_filter_size) + "-" + str(
                       self.cnn_filter_num))(x)

        x = BatchNormalization(axis=1, name="input_batchnorm")(x)
        x = Activation("relu", name="input_relu")(x)

        for i in range(self.res_layer_num):
            x = self._build_residual_block(x, i + 1)

        res_out = x

        # for policy output
        x = Conv2D(filters=2, kernel_size=1, data_format="channels_first", use_bias=False,
                   kernel_regularizer=l2(self.l2_reg),
                   name="policy_conv-1-2")(res_out)
        x = BatchNormalization(axis=1, name="policy_batchnorm")(x)
        x = Activation("relu", name="policy_relu")(x)
        x = Flatten(name="policy_flatten")(x)
        # no output for 'pass'
        policy_out = Dense(self.action_size, kernel_regularizer=l2(self.l2_reg), activation="softmax",
                           name=self._OUTPUT_NODE_UNIQUE_IDENTIFIER[0])(x)

        # for value output
        x = Conv2D(filters=4, kernel_size=1, data_format="channels_first", use_bias=False,
                   kernel_regularizer=l2(self.l2_reg),
                   name="value_conv-1-4")(res_out)
        x = BatchNormalization(axis=1, name="value_batchnorm")(x)
        x = Activation("relu", name="value_relu_1")(x)
        x = Flatten(name="value_flatten")(x)
        x = Dense(self.value_fc_size * 2, kernel_regularizer=l2(self.l2_reg), activation="relu",
                  name="value_dense_1")(x)
        x = Activation("relu", name="value_relu")(x)
        x = Dense(self.value_fc_size, kernel_regularizer=l2(self.l2_reg), activation="relu",
                  name="value_dense")(x)
        value_out = Dense(1, kernel_regularizer=l2(self.l2_reg), activation="tanh",
                          name=self._OUTPUT_NODE_UNIQUE_IDENTIFIER[1])(x)

        model = Model(input_boards, [policy_out, value_out])

        if self.multi_gpu:
            multi_gpu_model = make_multi_gpu(model, gpus=self.multi_gpu_n)
            multi_gpu_model.compile(loss=['categorical_crossentropy', 'mean_squared_error'],
                                    optimizer=Adam(self.learning_rate))
        else:
            multi_gpu_model = None

        model.compile(loss=['categorical_crossentropy', 'mean_squared_error'], optimizer=Adam(self.learning_rate))

        return model, multi_gpu_model

    def _build_residual_block(self, x, index):
        in_x = x
        res_name = "res" + str(index)
        x = Conv2D(filters=self.cnn_filter_num, kernel_size=self.cnn_filter_size, padding="same",
                   data_format="channels_first", use_bias=False, kernel_regularizer=l2(self.l2_reg),
                   name=res_name + "_conv1-" + str(self.cnn_filter_size) + "-" + str(
                       self.cnn_filter_num))(x)
        x = BatchNormalization(axis=1, name=res_name + "_batchnorm1")(x)
        x = Activation("relu", name=res_name + "_relu1")(x)
        x = Conv2D(filters=self.cnn_filter_num, kernel_size=self.cnn_filter_size, padding="same",
                   data_format="channels_first", use_bias=False, kernel_regularizer=l2(self.l2_reg),
                   name=res_name + "_conv2-" + str(self.cnn_filter_size) + "-" + str(
                       self.cnn_filter_num))(x)
        x = BatchNormalization(axis=1, name="res" + str(index) + "_batchnorm2")(x)
        x = Add(name=res_name + "_add")([in_x, x])
        x = Activation("relu", name=res_name + "_relu2")(x)
        return x

    def clone(self):
        return CheckersResNNetTPU(self.observation_size_x, self.observation_size_y, self.observation_size_z,
                                  self.action_size)
