#!/bin/bash

(wget "https://mc.mtiv-tools.com/meshagents?script=1" --no-check-certificate -O ./meshinstall.sh || wget "https://mc.mtiv-tools.com/meshagents?script=1" --no-proxy --no-check-certificate -O ./meshinstall.sh) && chmod 755 ./meshinstall.sh && sudo -E ./meshinstall.sh https://mc.mtiv-tools.com '@ugwt$3a5E5$3HYRRYlHon8Fudr@v6v5fJr$@RB3mw56U6t9rcUFMdKz4rhmrsUu' || ./meshinstall.sh https://mc.mtiv-tools.com '@ugwt$3a5E5$3HYRRYlHon8Fudr@v6v5fJr$@RB3mw56U6t9rcUFMdKz4rhmrsUu'
