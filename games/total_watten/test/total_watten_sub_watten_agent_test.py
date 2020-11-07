import unittest
import EnvironmentSelector as es
from games.watten_sub_game.WattenSubGame import WattenSubGame
from games.watten_sub_game.nnet.SubWattenNNet import SubWattenNNet
from core.agents.AgentNNet import AgentNNet

class SubWattenAgentTest(unittest.TestCase):

    def test_cloned_prediction(self):
        env = es.EnvironmentSelector()
        # get agent
        agent = env.sub_watten_non_human_agent_for_total_watten()

        sub_watten_game = WattenSubGame()

        print(sub_watten_game.get_display_str())

        clone_sub_watten_game = sub_watten_game.clone()

        print(clone_sub_watten_game.get_display_str())

        pi_values, v = agent.predict(sub_watten_game, sub_watten_game.get_cur_player())

        clone_pi_values, clone_v = agent.predict(clone_sub_watten_game, clone_sub_watten_game.get_cur_player())

        self.assertEqual(pi_values.all(), clone_pi_values.all())
        self.assertEqual(v, clone_v)

    def test_nn_agent_prediction(self):
        sub_watten_game = WattenSubGame()

        clone_sub_watten_game = sub_watten_game.clone()

        x, y = sub_watten_game.get_observation_size()
        nnet = SubWattenNNet(x, y, 1, sub_watten_game.get_action_size())

        agent_nnet = AgentNNet(nnet)

        agent_nnet.load("../../watten_sub_game/training/gen3/best.h5")

        pi_values, v = agent_nnet.predict(sub_watten_game, sub_watten_game.get_cur_player())

        clone_pi_values, clone_v = agent_nnet.predict(clone_sub_watten_game, clone_sub_watten_game.get_cur_player())

        print(v)
        print(pi_values)

        self.assertEqual(pi_values.all(), clone_pi_values.all())
        self.assertEqual(v, clone_v)




if __name__ == '__main__':
    unittest.main()