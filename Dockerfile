FROM ubuntu:18.04

WORKDIR /IasisInteractionSideEffectService
ADD . /IasisInteractionSideEffectService

RUN apt-get --assume-yes update
#RUN apt-get --assume-yes upgrade
RUN apt-get --assume-yes install python3 python3-flask python3-sparqlwrapper

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME IASISKG_ENDPOINT


# Run app.py when the container launches
CMD ./run_iasis_interactionSideEffects_service.sh

