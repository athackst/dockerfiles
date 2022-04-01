FROM jekyll/jekyll:pages AS dev

RUN apk update && apk add --no-cache \
    # development packages
    ruby-dev \
    gcc \
    make \
    curl \
    build-base \
    libc-dev \
    libffi-dev \
    zlib-dev \
    libxml2-dev \
    libgcrypt-dev \
    libxslt-dev \
    python3 \
    # pushing to git via ssh
    openssh \
    # permissions to install packages
    sudo \
    # tab completion inside the container
    git-bash-completion \
    shadow

# Set up development user.
ARG USERNAME=jekyll
RUN echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  && echo "source /usr/share/bash-completion/completions/git" >> /home/$USERNAME/.bashrc \
  && echo -e "if [ -f ~/.bash_aliases ]; then\n    . ~/.bash_aliases\nfi" >> /home/$USERNAME/.bashrc

# Get my aliases
RUN wget -O /etc/profile.d/git_aliases.sh https://github.com/athackst/workstation_setup/raw/main/user/.aliases/git_aliases.sh \
    && echo "source /etc/profile.d/git_aliases.sh" >> "/home/jekyll/.bashrc"

EXPOSE 4000

CMD ["bundle", "exec", "jekyll", "serve"]