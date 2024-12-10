### Install
Install dependencies:
```shell
pip install git+https://github.com/z80dev/boa-solidity.git
pip install -r requirements.in

solc-select install 0.8.18
solc-select use 0.8.18

npm install solidity-rlp@2.0.7
```

Install only `contracts/` folder from xdao:
```shell
echo "contracts/" >> .git/modules/contracts/xdao/info/sparse-checkout
rm -rf contracts/xdao
git submodule update
git submodule sync
```


### Run
```shell
python scripts/scrvusd/deploy.py
```
