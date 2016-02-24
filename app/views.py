from routefunc import base_section_files, ordered_menu_list, get_values
from apic_manager import apic
from app import app
from flask import render_template, g
import flask_sijax
import model
import traceback

#@app.route('/')
@app.route('/index')
def index():
    section_info = base_section_files()
    return render_template('index.html', title='Index', data=ordered_menu_list(section_info))


@flask_sijax.route(app, '/integration/create_access')
def create_access_vlan():
    def create_access_form_handler(obj_response, formvalues):
        values = get_values(formvalues)
        apic_object = apic.Apic()
        apic_object.login(app.apic_url, app.apic_user, app.apic_password)
        g.db = model.database
        g.db.connect()

        if values['operation'] == 'get_groups':
            try:
                tenants = apic_object.get_all_tenants()
                option_list = '<option value="">Select</option>'
                for tenant in tenants:
                    option_list += '<option value="' + str(tenant.dn) + '">' + tenant.name + '</option>'
                obj_response.html(".sel-group", option_list)
                obj_response.html("#div_create_vpc_access_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#div_create_vpc_access_response", '<label class="label label-danger" > '
                                                              '<i class="fa fa-times-circle"></i> '
                                                              'Can not create network: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_vpc_access':
            try:
                vpcs = model.vpc.select()
                option_list = '<option value="">Select</option>'
                for vpc in vpcs:
                    option_list += '<option value="' + str(vpc.id) + '">' + vpc.name + '</option>'
                obj_response.html("#sel_vpc_create_vpc_access", option_list)
                obj_response.html("#div_create_vpc_access_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#div_create_vpc_access_response", '<label class="label label-danger" > '
                                                              '<i class="fa fa-times-circle"></i> '
                                                              'Can not retrieve VPCs: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_networks':
            try:
                network_aps = apic_object.get_ap_by_tenant(values['sel_group_create_vpc_access'])
                if len(network_aps) > 0:
                    networks = apic_object.get_epg_by_ap(str(network_aps[0].dn))
                    option_list = '<option value="">Select</option>'
                    for network in networks:
                        option_list += '<option value="' + str(network.dn) + '">' + network.name + '</option>'
                    obj_response.html(".network", option_list)
                obj_response.html("#div_create_vpc_access_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#div_create_vpc_access_response", '<label class="label label-danger" > '
                                                                     '<i class="fa fa-times-circle"></i> '
                                                                     'Can not retrieve VPCs: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_vpcs':
            try:
                vpc_list = model.vpc.select()
                option_list = '<option value="">Select</option>'
                for vpc in vpc_list:
                   option_list += '<option value="' + str(vpc.id) + '">' + vpc.name + '</option>'
                obj_response.html(".sel-vpc", option_list)
                obj_response.html("#div_create_vpc_access_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#div_create_vpc_access_response", '<label class="label label-danger" > '
                                                                     '<i class="fa fa-times-circle"></i> '
                                                                     'Can not create retrieve ports: ' + e.message +
                                                                     '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_leafs':
            option_list = '<option value="">Select</option>'
            leafs = apic_object.get_leafs()
            for i in range(0, len(leafs[0])):
                option_list += '<option value="' + leafs[0][i] + '">' + leafs[1][i] + '</option>'
            obj_response.html("#sel_leaf_create_port_access", option_list)
            obj_response.html("#create_access_port_response", '')

        elif values['operation'] == 'get_ports':
            try:
                option_list = '<option value="">Select</option>'
                ports = apic_object.get_ports(values['sel_leaf_create_port_access'])
                for i in range(0, len(ports[0])):
                    port_list = model.port.select().where(model.port.port_dn == ports[0][i])
                    if len(port_list) > 0:
                        # Port already exists in database.. checking availability
                        port_o = port_list[0]
                        portxnetwork_list = model.portxnetwork.select().where(
                            model.portxnetwork.switch_port == port_o.id)
                        if port_o.assigned_vpc is None and len(portxnetwork_list) == 0:
                            option_list += '<option value="' + ports[0][i] + '">' + ports[1][i] + '</option>'
                    else:
                        # Port does not exist, it is available
                        option_list += '<option value="' + ports[0][i] + '">' + ports[1][i] + '</option>'
                obj_response.html("#sel_port_create_port_access", option_list)
                obj_response.html("#create_access_port_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#create_access_port_response", '<label class="label label-danger" > '
                                                             '<i class="fa fa-times-circle"></i> '
                                                             'Can not create access: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'create_port_access':
            try:
                # Verify if the port has been created
                port_list = model.port.select().where(model.port.port_dn == values['sel_port_create_port_access'])
                if len(port_list) == 0:
                    port_o = model.port.create(port_dn=values['sel_port_create_port_access'],
                                               assigned_vpc=None)
                else:
                    port_o = port_list[0]
                # Creates the association
                portxnetwork_o = model.portxnetwork.create(switch_port=port_o.id,
                                                           network=int(values['sel_network_create_port_access']))
                # TODO: ASSOCIATE EPG TO PORT IN APIC
                obj_response.html("#create_access_port_response", '<label class="label label-success" >'
                                                             '<i class="fa fa-check-circle"></i>Created</label>')
                obj_response.html("#sel_port_create_port_access", '')
                obj_response.script('$("#sel_network_create_port_access").val("")')
                obj_response.script('$("#sel_leaf_create_port_access").val("")')
                # Refresh the delete port select
                obj_response.script("get_port_accesses();")
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#create_access_port_response", '<label class="label label-danger" > '
                                                             '<i class="fa fa-times-circle"></i> '
                                                             'Can not create access: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'delete_port_access':
            try:
                # Deletes the association
                model.portxnetwork.delete().where(
                    model.portxnetwork.id == int(values['sel_delete_port_access'])).execute()
                # TODO: DE-ASSOCIATE EPG TO PORT IN APIC
                obj_response.html("#delete_port_access_response", '<label class="label label-success" >'
                                                             '<i class="fa fa-check-circle"></i>Created</label>')
                portxnetwork_list = model.portxnetwork.select()

                # Refresh the port selects
                obj_response.script("get_ports();get_port_accesses();")
                obj_response.html("#delete_access_port_response", '<label class="label label-success" > '
                                                                  '<i class="fa fa-check-circle"></i> '
                                                                  'Deleted</label>')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#delete_access_port_response", '<label class="label label-danger" > '
                                                                  '<i class="fa fa-times-circle"></i> '
                                                                  'Can not delete access: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_port_accesses':
            try:
                portxnetwork_list = model.portxnetwork.select()
                option_list = '<option value="">Select</option>'
                for portxnetwork in portxnetwork_list:
                    port_mo = apic_object.moDir.lookupByDn(portxnetwork.switch_port.port_dn)
                    option_list += '<option value="' + str(portxnetwork.id) + '">' + portxnetwork.network.name + ' - ' +\
                                   str(port_mo.id) + '</option>'
                obj_response.html("#sel_delete_port_access", option_list)
                obj_response.html("#delete_access_port_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#delete_access_port_response", '<label class="label label-danger" > '
                                                                  '<i class="fa fa-times-circle"></i> '
                                                                  'Can not retrieve port accesses: ' + e.message +
                                                                  '</label>')
        elif values['operation'] == 'create_vpc_access':
            try:
                vpcxnetwork_list = model.vpcxnetwork.select().where(
                    model.vpcxnetwork.network == values['sel_network_create_vpc_access'],
                    model.vpcxnetwork.vpc == values['sel_vpc_create_vpc_access'])
                # Check if already exists
                if len(vpcxnetwork_list) == 0:
                    vpcxnetwork_o = model.vpcxnetwork.create(network=int(values['sel_network_create_vpc_access']),
                                                             vpc=int(values['sel_vpc_create_vpc_access']))
                    # TODO: ASSOCIATE EPG TO VCP IN APIC
                    vpcxnetwork_list = model.vpcxnetwork.select()
                    option_list = '<option value="">Select</option>'
                    for vpcxnetwork in vpcxnetwork_list:
                        option_list += '<option value="' + str(vpcxnetwork.id) + '">' + vpcxnetwork.network.name + ' - ' \
                                  + vpcxnetwork.vpc.name + '</option>'
                    obj_response.html("#sel_delete_network_vpc_association", option_list)
                obj_response.html("#div_create_vpc_access_response", '<label class="label label-success" >'
                                                                     '<i class="fa fa-check-circle"></i>Created</label>')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#create_access_port_response", '<label class="label label-danger" > '
                                                                  '<i class="fa fa-times-circle"></i> '
                                                                  'Can not create access: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_network_vpc_associations':
            try:
                vpcxnetwork_list = model.vpcxnetwork.select()
                option_list = '<option value="">Select</option>'
                for vpcxnetwork in vpcxnetwork_list:
                   option_list += '<option value="' + str(vpcxnetwork.id) + '">' + vpcxnetwork.network.name + ' - ' \
                                  + vpcxnetwork.vpc.name + '</option>'
                obj_response.html("#sel_delete_network_vpc_association", option_list)
                obj_response.html("#div_delete_vpc_access_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#div_delete_vpc_access_response", '<label class="label label-danger" > '
                                                                     '<i class="fa fa-times-circle"></i> '
                                                                     'Can not create retrieve ports: ' + e.message +
                                                                     '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'delete_vpc_access':
            try:
                model.vpcxnetwork.delete().where(
                    model.vpcxnetwork.id == int(values['sel_delete_network_vpc_association'])).execute()
                # TODO: DE-ASSOCIATE EPG TO VCP IN APIC
                vpcxnetwork_list = model.vpcxnetwork.select()
                option_list = '<option value="">Select</option>'
                for vpcxnetwork in vpcxnetwork_list:
                   option_list += '<option value="' + str(vpcxnetwork.id) + '">' + vpcxnetwork.network.name + ' - ' \
                                  + vpcxnetwork.vpc.name + '</option>'
                obj_response.html("#sel_delete_network_vpc_association", option_list)
                obj_response.html("#div_delete_vpc_access_response", '<label class="label label-success" >'
                                                                     '<i class="fa fa-check-circle"></i>Deleted</label>')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#div_delete_vpc_access_response", '<label class="label label-danger" > '
                                                                  '<i class="fa fa-times-circle"></i> '
                                                                  'Can not create access: ' + e.message + '</label>')
            finally:
                g.db.close()

    if g.sijax.is_sijax_request:
        g.sijax.register_callback('create_access_form_handler', create_access_form_handler)
        return g.sijax.process_request()

    section_info = base_section_files()
    return render_template('create-access.html', title='Create access VLAN', data=ordered_menu_list(section_info))


@flask_sijax.route(app, '/')
@flask_sijax.route(app, '/integration/create_network')
def create_network():
    def network_form_handler(obj_response, formvalues):
        values = get_values(formvalues)
        apic_object = apic.Apic()
        apic_object.login(app.apic_url, app.apic_user, app.apic_password)
        g.db = model.database
        g.db.connect()

        if values['operation'] == 'get_groups':
            try:
                tenants = apic_object.get_all_tenants()
                option_list = '<option value="">Select</option>'
                for tenant in tenants:
                    option_list += '<option value="' + str(tenant.dn) + '">' + tenant.name + '</option>'
                obj_response.html(".sel-group", option_list)
                obj_response.html("#create_network_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#create_network_response", '<label class="label label-danger" > '
                                                              '<i class="fa fa-times-circle"></i> '
                                                              'Can not create network: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'create_group':
            try:
                apic_object.create_group(values['create_group_name'])
                obj_response.html("#create_group_response", '<label class="label label-success" > '
                                                            '<i class="fa fa-check-circle"></i> Created </label>')

                obj_response.script('get_groups();')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#create_group_response", '<label class="label label-danger" > '
                                                              '<i class="fa fa-times-circle">'
                                                              '</i> Can not create group: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'delete_group':
            try:
                apic_object.delete_tenant(values['sel_delete_group_name'])
                obj_response.script("get_groups();")
                obj_response.html("#delete_group_response", '<label class="label label-success" > '
                                                            '<i class="fa fa-check-circle"></i> Deleted </label>')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#delete_group_response", '<label class="label label-danger" > '
                                                              '<i class="fa fa-times-circle">'
                                                              '</i> Can not create network: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'create_network':
            try:
                network_object = model.network(name=values['create_network_name'],
                                               encapsulation=int(values['create_network_encapsulation']),
                                               group=values['sel_create_network_group'])
                apic_object.create_network(network_object)
                obj_response.html("#create_network_response", '<label class="label label-success" > '
                                                              '<i class="fa fa-check-circle"></i> Created </label>')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#create_network_response", '<label class="label label-danger" > '
                                                              '<i class="fa fa-times-circle"></i> '
                                                              'Can not create network: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_sel_delete_networks':
            try:
                network_aps = apic_object.get_ap_by_tenant(values['sel_delete_network_group'])
                if len(network_aps) > 0:
                    networks = apic_object.get_epg_by_ap(str(network_aps[0].dn))
                    option_list = '<option value="">Select</option>'
                    for network in networks:
                        option_list += '<option value="' + str(network.dn) + '">' + network.name + '</option>'
                    obj_response.html("#sel_delete_network_name", option_list)
                obj_response.html("#delete_network_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#delete_network_response", '<label class="label label-danger" > '
                                                                     '<i class="fa fa-times-circle"></i> '
                                                                     'Can not retrieve networks: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'delete_network':
            try:
                apic_object.delete_epg(values['sel_delete_network_name'])
                obj_response.script('get_sel_delete_networks()')
                obj_response.html("#delete_network_response", '<label class="label label-success" > '
                                                              '<i class="fa fa-check-circle"></i> Deleted </label>')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#delete_network_response", '<label class="label label-danger" > '
                                                              '<i class="fa fa-times-circle"></i> '
                                                              'Can not create network: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_leafs':
            option_list = '<option value="">Select</option>'
            leafs = apic_object.get_leafs()
            for i in range(0, len(leafs[0])):
                option_list += '<option value="' + leafs[0][i] + '">' + leafs[1][i] + '</option>'
            obj_response.html("#sel_leaf_create_vpc", option_list)
            obj_response.html("#create_vpc_response", '')

        elif values['operation'] == 'get_ports':
            # """ Returns only available ports """
            try:
                option_list = '<option value="">Select</option>'
                ports = apic_object.get_ports(values['sel_leaf_create_vpc'])
                for i in range(0, len(ports[0])):
                    port_list = model.port.select().where(model.port.port_dn == ports[0][i])
                    if len(port_list) > 0:
                        # Port already exists in database.. checking availability
                        port_o = port_list[0]
                        portxnetwork_list = model.portxnetwork.select().where(
                            model.portxnetwork.switch_port == port_o.id)
                        if port_o.assigned_vpc is None and len(portxnetwork_list) == 0:
                            option_list += '<option value="' + ports[0][i] + '">' + ports[1][i] + '</option>'
                    else:
                        # Port does not exist, it is available
                        option_list += '<option value="' + ports[0][i] + '">' + ports[1][i] + '</option>'
                obj_response.html("#sel_port_create_vpc", option_list)
                obj_response.html("#create_vpc_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#create_vpc_response", '<label class="label label-danger" > '
                                                          '<i class="fa fa-times-circle"></i> '
                                                          'Can not retrieve ports: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'create_vpc':
            try:
                vpc_object = model.vpc.create(name=values['create_vpc_name'])
                selected_ports = str(values['port_dns']).split(';')
                for port_dn in selected_ports:
                    if len(port_dn) > 0:
                        # Check if port already exists
                        port_list = model.port.select().where(model.port.port_dn == port_dn)
                        if len(port_list) > 0:
                            model.port.update(assigned_vpc=vpc_object.id).where(model.port.port_dn == port_dn).execute()
                        else:
                            model.port.create(port_dn=port_dn,
                                              assigned_vpc=vpc_object.id)
                # TODO: Create VPC in APIC
                vpc_list = model.vpc.select()
                option_list = '<option value="">Select</option>'
                for vpc in vpc_list:
                   option_list += '<option value="' + str(vpc.id) + '">' + vpc.name + '</option>'
                obj_response.html(".sel-vpc", option_list)
                table = '<thead>' \
                            '<tr>' \
                                '<th>Switch</th>' \
                                '<th>Port</th>' \
                            '</tr>' \
                        '</thead>' \
                        '<tbody>' \
                        '<tr></tr>' \
                        '</tbody>'
                obj_response.html("#vpc_ports", table)
                obj_response.html("#sel_port_create_vpc", '')
                obj_response.script('$("#sel_leaf_create_vpc").val("")')
                obj_response.html("#create_vpc_response", '<label class="label label-success" > '
                                                          '<i class="fa fa-check-circle"></i> Created </label>')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#create_vpc_response", '<label class="label label-danger" > '
                                                          '<i class="fa fa-times-circle"></i> '
                                                          'Can not create vpc: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_delete_vpc_assigned_ports':
            try:
                port_list = model.port.select().where(model.port.assigned_vpc == values['sel_delete_vpc_name'])
                table = '<thead>' \
                            '<tr>' \
                                '<th>Switch</th>' \
                                '<th>Port</th>' \
                            '</tr>' \
                        '</thead>' \
                        '<tbody>'
                for port in port_list:
                    if len(port.port_dn) > 0:
                        port_mo = apic_object.moDir.lookupByDn(port.port_dn)
                        switch_mo = apic_object.get_switch_by_port(port)
                        table += '<tr><td>' + str(switch_mo.rn) + '</td><td>' + port_mo.id + '</td></tr>'

                table += '</tbody>'
                obj_response.html("#delete_vpc_ports", table)
                obj_response.html("#delete_vpc_response", '')

            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#delete_vpc_response", '<label class="label label-danger" > '
                                                          '<i class="fa fa-times-circle"></i> '
                                                          'Can not create retrieve ports: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'get_vpcs':
            try:
                vpc_list = model.vpc.select()
                option_list = '<option value="">Select</option>'
                for vpc in vpc_list:
                   option_list += '<option value="' + str(vpc.id) + '">' + vpc.name + '</option>'
                obj_response.html(".sel-vpc", option_list)
                obj_response.html("#delete_vpc_response", '')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#delete_vpc_response", '<label class="label label-danger" > '
                                                          '<i class="fa fa-times-circle"></i> '
                                                          'Can not create retrieve ports: ' + e.message + '</label>')
            finally:
                g.db.close()

        elif values['operation'] == 'delete_vpc':
            try:
                # TODO: Delete VPC from APIC
                model.vpc.delete().where(model.vpc.id == int(values['sel_delete_vpc_name'])).execute()
                model.port.update(assigned_vpc=None).where(
                    model.port.assigned_vpc == int(values['sel_delete_vpc_name'])).execute()
                vpc_list = model.vpc.select()
                option_list = '<option value="">Select</option>'
                for vpc in vpc_list:
                    option_list += '<option value="' + str(vpc.id) + '">' + vpc.name + '</option>'
                obj_response.html(".sel-vpc", option_list)
                obj_response.html("#delete_vpc_ports", '')
                obj_response.html("#delete_vpc_response", '<label class="label label-success" > '
                                                          '<i class="fa fa-check-circle"></i> Created </label>')
            except Exception as e:
                print traceback.print_exc()
                obj_response.html("#delete_vpc_response", '<label class="label label-danger" > '
                                                          '<i class="fa fa-times-circle"></i> '
                                                          'Can not delete vpc: ' + e.message + '</label>')
            finally:
                g.db.close()



    if g.sijax.is_sijax_request:
        g.sijax.register_callback('network_form_handler', network_form_handler)
        return g.sijax.process_request()

    section_info = base_section_files()
    return render_template('create-network.html', title='Create network', data=ordered_menu_list(section_info))

@app.before_request
def before_request():
    if not model.network.table_exists():
        model.create_tables()
