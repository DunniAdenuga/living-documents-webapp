# start from an official image
FROM node:11

# location of source code
RUN mkdir -p /opt/services/nodeapp
WORKDIR /opt/services/nodeapp

# copy code over
COPY . /opt/services/nodeapp

# install stuff
RUN npm install -g webpack
RUN npm link webpack
RUN npm install -g webpack-cli
RUN npm link webpack-cli
RUN npm install -g webpack-dev-server
RUN npm link webpack-dev-server
RUN npm install --save-dev webpack-merge
RUN npm install --save-dev eslint@5
RUN npm install eslint-plugin-vue
RUN npm install babel-eslint

RUN npm install

# open port
ENV PORT 9090

CMD ["npm", "start"]
