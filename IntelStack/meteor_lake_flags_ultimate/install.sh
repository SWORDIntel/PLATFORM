#!/bin/bash
echo "Installing Meteor Lake Compiler Flags..."
cp METEOR_LAKE_COMPLETE_FLAGS.sh ~/.meteor_lake_flags.sh
echo "source ~/.meteor_lake_flags.sh" >> ~/.bashrc
echo "✓ Installed! Restart shell or run: source ~/.meteor_lake_flags.sh"
